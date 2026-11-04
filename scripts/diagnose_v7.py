"""Diagnostics of the v7 model at alpha* (descriptive, not a calibration result).

For the run at the v7 margin (same code path as scripts/calibrate_margin.py):
- monthly redispatch volume (up + down) and its split north / south of 51.0 N by bus latitude;
- per branch: hours over the margin before redispatch (by quarter), max loading, length of
  overload; the 25 most often binding branches with their voltage and location;
- offshore: hourly offshore output at landing buses vs curtailment; PTDF sensitivity of each
  landing bus on the 25 most binding branches (how much 1 MW at the landing loads the line).
Writes results/diagnostics/v7_alpha_<a>.json.
"""

from __future__ import annotations

import argparse
import json
import subprocess

import numpy as np
import pandas as pd

from netzfix.config import DATA_PROCESSED, RESULTS, load_config
from netzfix.server.state import Playground
from netzfix.sim.behaviours import Context
from netzfix.sim.redispatch import CostRule, redispatch


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--alpha", type=float, default=0.991)
    a = ap.parse_args()
    cfg = load_config()["redispatch"]
    pg = Playground()
    ctx = Context(ts=pg.ts, capacity=pg.capacity, regional_cf=pg.regional_cf)
    r = pg.simulate(ctx, track_carriers=True)
    costs = CostRule.from_config(pg.ts.index, cfg["prices"])
    down = r.down_bus if r.down_bus is not None else r.disp_bus
    rd = redispatch(r.flow, pg.ptdf, pg.s_nom, r.headroom_bus, down, r.res_bus,
                    limit_pu=a.alpha, costs=costs)
    n = pg.grid.network
    bus_y = n.buses.y.reindex(pg.buses).to_numpy()
    vol = rd.up + rd.down_disp + rd.down_res                                  # T x buses
    local = pg.ts.index.tz_convert("Europe/Berlin")
    month = local.month.to_numpy()
    north = bus_y >= 51.0
    monthly = {int(m): {"total_gwh": float(vol[month == m].sum() / 1e3),
                        "north_gwh": float(vol[month == m][:, north].sum() / 1e3),
                        "south_gwh": float(vol[month == m][:, ~north].sum() / 1e3),
                        "curtail_gwh": float(rd.down_res[month == m].sum() / 1e3)}
               for m in range(1, 13)}
    L = a.alpha * pg.s_nom
    over = np.abs(r.flow) > L + 1e-6                                          # T x branches
    q = local.quarter.to_numpy()
    hours = over.sum(axis=0)
    top = np.argsort(-hours)[:25]
    br = []
    lines, trafos = n.lines, n.transformers
    for k in top:
        name = pg.branches[k]
        comp, idx = name.split(":", 1)
        tab = lines if comp == "Line" else trafos
        b0, b1 = tab.at[idx, "bus0"], tab.at[idx, "bus1"]
        br.append({"branch": name, "hours_over": int(hours[k]),
                   "by_quarter": {int(j): int(over[q == j, k].sum()) for j in (1, 2, 3, 4)},
                   "max_loading_pu_of_s_nom": float(np.abs(r.flow[:, k]).max() / pg.s_nom[k]),
                   "s_nom": float(pg.s_nom[k]),
                   "v_nom": float(n.buses.at[b0, "v_nom"]),
                   "bus0": b0, "bus1": b1,
                   "lat": float((n.buses.at[b0, "y"] + n.buses.at[b1, "y"]) / 2),
                   "lon": float((n.buses.at[b0, "x"] + n.buses.at[b1, "x"]) / 2)})
    conn = pd.read_csv(DATA_PROCESSED / "offshore_connections.csv").dropna(subset=["landing_bus"])
    land = sorted(set(conn["landing_bus"]) & set(pg.buses))
    bidx = {b: i for i, b in enumerate(pg.buses)}
    sens = {b: {pg.branches[k]: float(pg.ptdf[k, bidx[b]]) for k in top[:10]} for b in land}
    off = r.res_by_carrier.get("wind_offshore") if r.res_by_carrier else None
    off_info = {}
    if off is not None:
        cut = rd.down_res * np.where(r.res_bus > 1e-9, off / np.maximum(r.res_bus, 1e-9), 0.0)
        for b in land:
            i = bidx[b]
            off_info[b] = {"offshore_twh": float(off[:, i].sum() / 1e6),
                           "curtailed_gwh": float(cut[:, i].sum() / 1e3),
                           "max_abs_ptdf_on_top10": float(max(abs(v) for v in sens[b].values()))}
    out = {"alpha": a.alpha,
           "commit": subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                                    text=True).stdout.strip(),
           "monthly": monthly, "top_branches": br, "offshore_landings": off_info,
           "landing_sensitivity_top10": sens}
    d = RESULTS / "diagnostics"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"v7_alpha_{a.alpha:.3f}.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("written", d / f"v7_alpha_{a.alpha:.3f}.json")


if __name__ == "__main__":
    main()
