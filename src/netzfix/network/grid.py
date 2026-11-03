"""Static German transmission grid from the PyPSA-Eur OSM network (v0.7), as a PyPSA Network.

What is built (see vault/project/Assumptions.md, A4 and A17-A19):
- Buses: German substations (country == DE) in the largest AC-connected component.
- Lines: AC lines with both ends in that component (s_nom, r, x, b from the OSM dataset).
- Transformers: OSM s_nom; x = 0.1 p.u. (PyPSA-Eur default `transformers.x`, config at v2026.09.0).
- Neighbours (A18 v1): each AC neighbour's own OSM grid is Kron-reduced onto its border substations
  plus one hub (the bus nearest the centroid of its grid component). The result is an exact DC
  equivalent seen from the border: equivalent lines `EQ-...` (no thermal limit) between the kept
  buses `NB-<CC>:<osm bus>`, plus the real cross-border lines. The country's measured physical
  exchange is injected at its hub(s). A first version with one copper-plate node per country gave
  ~4 GW of fake transit through NL (2026-11-03), hence the reduction.
  Not modelled: loop flows between neighbours (third-country paths); the measured border flows
  contain them in total but the routing inside DE does not see them.
- HVDC interconnectors are controllable: their share is injected at the German converter bus.
- `borders` lists every border element with `inject_bus` (hub for AC, converter bus for HVDC).
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
S_BASE = 100.0          # MVA, per-unit base for the Kron reduction
EQ_V = 380.0            # kV at which equivalent-line reactances are expressed
EQ_S_NOM = 1e6          # MVA: equivalent lines are fictitious, never a constraint


def _kron_equivalent(cc: str, boundary: list[str], b: pd.DataFrame, ln: pd.DataFrame,
                     tr: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, str]]:
    """Reduce country `cc`'s AC grid onto `boundary` buses + one hub per grid component.

    Returns (kept buses [id, x, y, v_nom], equivalent lines [bus0, bus1, x_ohm],
    map boundary bus -> hub bus). Susceptances in p.u. on S_BASE; line x in ohm at bus0's kV.
    """
    import scipy.sparse as sp
    from scipy.sparse.linalg import splu

    bus = b[(b.country == cc) & (b.dc == "f")].set_index("bus_id")
    lc = ln[ln.bus0.isin(bus.index) & ln.bus1.isin(bus.index)]
    tc = tr[tr.bus0.isin(bus.index) & tr.bus1.isin(bus.index)]
    g = nx.Graph()
    g.add_edges_from(zip(lc.bus0, lc.bus1, strict=True))
    g.add_edges_from(zip(tc.bus0, tc.bus1, strict=True))
    g.add_nodes_from(boundary)
    kept, eq, hub_of = [], [], {}
    for comp in nx.connected_components(g):
        bnd = [x for x in boundary if x in comp]
        if not bnd:
            continue
        cb = bus.loc[sorted(comp)]
        cx, cy = cb.x.mean(), cb.y.mean()
        hub = ((cb.x - cx) ** 2 + (cb.y - cy) ** 2).idxmin()
        K = list(dict.fromkeys(bnd + [hub]))
        order = K + [x for x in cb.index if x not in K]
        idx = {x: i for i, x in enumerate(order)}
        rows, cols, vals = [], [], []

        def add(i: int, j: int, y: float, rows=rows, cols=cols, vals=vals) -> None:
            rows.extend([i, j, i, j])
            cols.extend([j, i, i, j])
            vals.extend([-y, -y, y, y])

        for r in lc[lc.bus0.isin(comp)].itertuples():
            z_base = float(bus.at[r.bus0, "voltage"]) ** 2 / S_BASE
            add(idx[r.bus0], idx[r.bus1], 1.0 / max(float(r.x) / z_base, 1e-6))
        for r in tc[tc.bus0.isin(comp)].itertuples():
            add(idx[r.bus0], idx[r.bus1], float(r.s_nom) / (TRANSFORMER_X_PU * S_BASE))
        nb = len(order)
        B = sp.csc_matrix((vals, (rows, cols)), shape=(nb, nb))
        k = len(K)
        if nb > k:
            BKK, BKI = B[:k, :k].toarray(), B[:k, k:]
            BII, BIK = B[k:, k:], B[k:, :k]
            red = BKK - BKI @ splu(BII.tocsc()).solve(BIK.toarray())
        else:
            red = B.toarray()
        z_eq = EQ_V ** 2 / S_BASE
        scale = np.abs(np.diag(red)).max()
        for i in range(k):
            for j in range(i + 1, k):
                y = -red[i, j]
                if y > 1e-9 * scale:
                    eq.append({"bus0": K[i], "bus1": K[j], "x_ohm": z_eq / y})
        kept += [{"id": x, "x": bus.at[x, "x"], "y": bus.at[x, "y"],
                  "v_nom": float(bus.at[x, "voltage"])} for x in K]
        for x in bnd:
            hub_of[x] = hub
    return pd.DataFrame(kept).drop_duplicates("id"), pd.DataFrame(eq), hub_of


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

    # Border points: cross-border AC lines, kept as real lines to one virtual bus per country ...
    rows = []
    cross = ln[ln.bus0.isin(main) != ln.bus1.isin(main)]
    cross = cross[(cross.bus0.isin(main) | cross.bus1.isin(main))].set_index("line_id")
    ends: dict[str, list[str]] = {}
    for _, r in cross.iterrows():
        other = r.bus1 if r.bus0 in main else r.bus0
        ends.setdefault(country.get(other, "?"), []).append(other)
    hub_of: dict[str, str] = {}
    for cc, others in ends.items():
        kept, eq, hubs = _kron_equivalent(cc, list(dict.fromkeys(others)), b, ln, tr)
        nm = {x: f"NB-{cc}:{x}" for x in kept.id}
        n.add("Bus", [nm[x] for x in kept.id], v_nom=kept.v_nom.to_numpy(),
              x=kept.x.to_numpy(), y=kept.y.to_numpy(), carrier="AC", country=cc)
        if len(eq):
            n.add("Line", [f"EQ-{cc}-{i}" for i in range(len(eq))],
                  bus0=[nm[x] for x in eq.bus0], bus1=[nm[x] for x in eq.bus1],
                  x=eq.x_ohm.to_numpy(), r=0.0, s_nom=EQ_S_NOM, carrier="equivalent")
        hub_of.update({x: nm[h] for x, h in hubs.items()})
    for lid, r in cross.iterrows():
        de_bus, other = (r.bus0, r.bus1) if r.bus0 in main else (r.bus1, r.bus0)
        rows.append({"border_id": lid, "bus": de_bus, "country": country.get(other, "?"),
                     "capacity_mw": float(r.s_nom), "kind": "AC line",
                     "inject_bus": hub_of[other]})
    ac_x = cross.copy()
    fname = {o: f"NB-{country.get(o)}:{o}" for os_ in ends.values() for o in os_}
    ac_x["fb0"] = [fname.get(r.bus0, r.bus0) for r in ac_x.itertuples()]
    ac_x["fb1"] = [fname.get(r.bus1, r.bus1) for r in ac_x.itertuples()]
    n.add("Line", ac_x.index, bus0=ac_x.fb0, bus1=ac_x.fb1, s_nom=ac_x.s_nom, r=ac_x.r,
          x=ac_x.x, b=ac_x.b, length=ac_x.length / 1e3, carrier="AC",
          num_parallel=ac_x.circuits.astype(float))
    # ... and HVDC interconnectors: DE DC bus -> converter -> DE AC bus in the main component
    flipped = cv[["bus1", "bus0"]].set_axis(["bus0", "bus1"], axis=1)
    conv = pd.concat([cv[["bus0", "bus1"]], flipped])
    dc_to_ac = conv[conv.bus1.isin(main)].set_index("bus0")["bus1"].to_dict()
    for lid, r in lk.set_index("link_id").iterrows():
        for de_dc, other in ((r.bus0, r.bus1), (r.bus1, r.bus0)):
            if de_dc in de and other not in de and de_dc in dc_to_ac:
                rows.append({"border_id": lid, "bus": dc_to_ac[de_dc],
                             "country": country.get(other, "?"),
                             "capacity_mw": float(r.p_nom), "kind": "HVDC link",
                             "inject_bus": dc_to_ac[de_dc]})
    borders = pd.DataFrame(rows)

    geom = pd.concat([ln_in["geometry"], tr_in["geometry"], cross["geometry"]])
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
