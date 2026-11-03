"""Static German transmission grid from the PyPSA-Eur OSM network (v0.7), as a PyPSA Network.

What is built (see vault/project/Assumptions.md, A4 and A17-A19):
- Buses: German substations (country == DE) in the largest AC-connected component.
- Lines: AC lines with both ends in that component (s_nom, r, x, b from the OSM dataset).
- Transformers: OSM s_nom; x = 0.1 p.u. (PyPSA-Eur default `transformers.x`, config at v2026.09.0).
- Border points: the German end of each cross-border AC line and each HVDC interconnector (via its
  AC/DC converter). Imports/exports are injected here; neighbouring grids are not modelled (A18).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
import pypsa

from netzfix.config import DATA_PROCESSED
from netzfix.data import osm_grid

TRANSFORMER_X_PU = 0.1  # PyPSA-Eur config.default.yaml `transformers.x` (v2026.09.0)


@dataclass
class Grid:
    network: pypsa.Network
    borders: pd.DataFrame       # border_id, bus, country, capacity_mw, kind
    line_geometry: pd.Series    # branch id -> WKT linestring (lines and transformers)
    dropped_buses: list[str]


def _read(name: str) -> pd.DataFrame:
    return pd.read_csv(osm_grid.raw_dir() / name, quotechar="'")


def build() -> Grid:
    osm_grid.download()
    b, ln, lk, tr, cv = (_read(f) for f in
                         ("buses.csv", "lines.csv", "links.csv", "transformers.csv",
                          "converters.csv"))
    country = b.set_index("bus_id")["country"]
    de = set(b.loc[b.country == "DE", "bus_id"])

    ln_in = ln[ln.bus0.isin(de) & ln.bus1.isin(de)]
    tr_in = tr[tr.bus0.isin(de) & tr.bus1.isin(de)]
    g = nx.Graph()
    g.add_nodes_from(de)
    g.add_edges_from(zip(ln_in.bus0, ln_in.bus1, strict=True))
    g.add_edges_from(zip(tr_in.bus0, tr_in.bus1, strict=True))
    main = max(nx.connected_components(g), key=len)
    dropped = sorted(de - main)

    bus = b[b.bus_id.isin(main)].set_index("bus_id")
    ln_in = ln_in[ln_in.bus0.isin(main) & ln_in.bus1.isin(main)].set_index("line_id")
    tr_in = tr_in[tr_in.bus0.isin(main) & tr_in.bus1.isin(main)].set_index("transformer_id")

    n = pypsa.Network()
    n.add("Carrier", "AC")
    n.add("Bus", bus.index, v_nom=bus.voltage.astype(float), x=bus.x, y=bus.y,
          carrier="AC", country="DE")
    n.add("Line", ln_in.index, bus0=ln_in.bus0, bus1=ln_in.bus1, s_nom=ln_in.s_nom,
          r=ln_in.r, x=ln_in.x, b=ln_in.b, length=ln_in.length / 1e3, carrier="AC",
          num_parallel=ln_in.circuits.astype(float))
    n.add("Transformer", tr_in.index, bus0=tr_in.bus0, bus1=tr_in.bus1, s_nom=tr_in.s_nom,
          x=TRANSFORMER_X_PU, r=0.0, model="t")

    # Border points: cross-border AC lines (German end) ...
    rows = []
    cross = ln[ln.bus0.isin(main) != ln.bus1.isin(main)]
    cross = cross[cross.bus0.isin(main) | cross.bus1.isin(main)]
    for lid, r in cross.set_index("line_id").iterrows():
        de_bus, other = (r.bus0, r.bus1) if r.bus0 in main else (r.bus1, r.bus0)
        rows.append({"border_id": lid, "bus": de_bus, "country": country.get(other, "?"),
                     "capacity_mw": float(r.s_nom), "kind": "AC line"})
    # ... and HVDC interconnectors: DE DC bus -> converter -> DE AC bus in the main component
    flipped = cv[["bus1", "bus0"]].set_axis(["bus0", "bus1"], axis=1)
    conv = pd.concat([cv[["bus0", "bus1"]], flipped])
    dc_to_ac = conv[conv.bus1.isin(main)].set_index("bus0")["bus1"].to_dict()
    for lid, r in lk.set_index("link_id").iterrows():
        for de_dc, other in ((r.bus0, r.bus1), (r.bus1, r.bus0)):
            if de_dc in de and other not in de and de_dc in dc_to_ac:
                rows.append({"border_id": lid, "bus": dc_to_ac[de_dc],
                             "country": country.get(other, "?"),
                             "capacity_mw": float(r.p_nom), "kind": "HVDC link"})
    borders = pd.DataFrame(rows)

    geom = pd.concat([ln_in["geometry"], tr_in["geometry"]])
    return Grid(n, borders, geom, dropped)


def save(grid: Grid, out_dir: Path | None = None) -> Path:
    out = out_dir or DATA_PROCESSED / f"grid_DE_osm{osm_grid.VERSION}"
    out.mkdir(parents=True, exist_ok=True)
    grid.network.export_to_netcdf(out / "network.nc")
    grid.borders.to_csv(out / "borders.csv", index=False)
    grid.line_geometry.rename("wkt").to_frame().to_parquet(out / "branch_geometry.parquet")
    pd.Series(grid.dropped_buses, name="bus").to_csv(out / "dropped_buses.csv", index=False)
    return out


def load(out_dir: Path | None = None) -> Grid:
    out = out_dir or DATA_PROCESSED / f"grid_DE_osm{osm_grid.VERSION}"
    if not (out / "network.nc").exists():
        save(build(), out)
    n = pypsa.Network(str(out / "network.nc"))
    return Grid(n, pd.read_csv(out / "borders.csv"),
                pd.read_parquet(out / "branch_geometry.parquet")["wkt"],
                pd.read_csv(out / "dropped_buses.csv")["bus"].tolist())


def ptdf(n: pypsa.Network) -> tuple[np.ndarray, list[str], list[str]]:
    """Dense PTDF (branches x buses) of the single AC sub-network, plus branch and bus labels.

    Branch labels are "Line:<id>" / "Transformer:<id>". Injections must sum to zero per snapshot
    (the simulation guarantees this), so the slack choice does not affect flows.
    """
    n.determine_network_topology()
    if len(n.sub_networks) != 1:
        raise ValueError(f"expected one AC sub-network, got {len(n.sub_networks)}")
    sn = n.sub_networks.obj.iloc[0]
    sn.calculate_PTDF()
    branches = [f"{c}:{i}" for c, i in sn.branches_i()]
    return np.asarray(sn.PTDF), branches, list(sn.buses_o)


if __name__ == "__main__":
    gr = build()
    out = save(gr)
    n = gr.network
    print(out)
    print(f"buses {len(n.buses)}, lines {len(n.lines)}, transformers {len(n.transformers)}, "
          f"border points {len(gr.borders)}, dropped buses {len(gr.dropped_buses)}")
    print(gr.borders.groupby(["country", "kind"]).capacity_mw.agg(["count", "sum"]).to_string())
