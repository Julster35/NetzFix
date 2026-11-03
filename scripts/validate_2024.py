"""Validate the 2024 'as is' playground against published 2024 figures.

Usage: uv run python scripts/validate_2024.py
Writes results/validation_2024/summary.json (+ redispatch_by_month.csv, unresolved_branches.csv).

Reference values (held PDFs in vault/literature/pdfs; PDF page numbers):
- BNetzA/BKartA Monitoringbericht 2025 (covers 2024):
  p. 23: congestion-management measures 2024 ~30,320 GWh (redispatch with market and reserve
         plants + countertrading); 2023: 34,298 GWh.
  p. 22: congestion-management costs 2024 ~2.9 bn EUR.
  p. 23: cross-border trade 2024 realised exchange: exports 37.6 TWh, imports 64.9 TWh.
  p. 18: TSO circuit length 38.4 thousand km (2024); peak load 75.8 GW on 15 Jan 2024 11:30-11:45.
The model's redispatch is a minimum-volume lower bound, not German practice (see
src/netzfix/sim/redispatch.py); it checks whether the grid model produces congestion of the
right order of magnitude.
"""

from __future__ import annotations

import json
import subprocess
import time

import numpy as np
import pandas as pd

from netzfix.config import RESULTS
from netzfix.server.state import Playground
from netzfix.sim.behaviours import Context
from netzfix.sim.engine import historical_import, simulate
from netzfix.sim.redispatch import redispatch

REF = {
    "congestion_management_gwh": (30320, "Monitoringbericht 2025, PDF p. 23"),
    "net_import_twh": (64.9 - 37.6,
                       "Monitoringbericht 2025, PDF p. 23 (imports 64.9 - exports 37.6)"),
    "tso_circuit_km": (38400, "Monitoringbericht 2025, PDF p. 18"),
    "peak_load_gw": (75.8, "Monitoringbericht 2025, PDF p. 18 (quarter-hour, 15 Jan 11:30-11:45)"),
}


def main() -> None:
    out_dir = RESULTS / "validation_2024"
    out_dir.mkdir(parents=True, exist_ok=True)
    pg = Playground()
    n = pg.grid.network
    ctx = Context(ts=pg.ts, capacity=pg.capacity)
    r = simulate(pg.assets(), pg.buses, pg.ptdf, pg.branches, pg.s_nom, pg.grid.borders, ctx)
    lines = n.lines
    model = {
        "tso_circuit_km": float((lines.length * lines.num_parallel).sum()),
        "peak_load_gw": float(pg.ts.load.max() / 1e3),
        "net_import_twh": float(historical_import(pg.ts).sum() / 1e6),
        "line_hours_over_100pct_before": int((r.loading > 1).sum()),
        "line_hours_over_70pct_before": int((r.loading > 0.7).sum()),
    }
    runs = {}
    month = pg.ts.index.tz_convert("Europe/Berlin").month
    monthly = {}
    unresolved_rows = []
    for lim in (1.0, 0.7):
        t0 = time.time()
        rd = redispatch(r.flow, pg.ptdf, pg.s_nom, r.headroom_bus, r.disp_bus, r.res_bus,
                        limit_pu=lim)
        v = rd.volume_twh()
        after = np.abs(rd.flow) / pg.s_nom
        runs[f"limit_{lim}"] = {
            "seconds": round(time.time() - t0, 1),
            "volume_twh": {k: round(x, 3) for k, x in v.items()},
            "hours_with_redispatch": int((rd.up.sum(axis=1) > 0.5).sum()),
            "unresolved_mwh": round(float(rd.unresolved.sum()), 1),
            "hours_unresolved": int((rd.unresolved > 0.5).sum()),
            "line_hours_over_limit_after": int((after > lim + 1e-3).sum()),
        }
        vol = pd.Series((rd.up + rd.down_disp + rd.down_res).sum(axis=1), index=month)
        monthly[f"limit_{lim}_up_plus_down_gwh"] = vol.groupby(level=0).sum() / 1e3
        over = (after > lim + 1e-3)
        for k in np.flatnonzero(over.any(axis=0)):
            comp, bid = pg.branches[k].split(":", 1)
            df = n.lines if comp == "Line" else n.transformers
            unresolved_rows.append({
                "limit": lim, "branch": pg.branches[k], "hours": int(over[:, k].sum()),
                "v_kv": float(n.buses.at[df.at[bid, "bus0"], "v_nom"]),
                "s_nom": float(pg.s_nom[k]), "max_loading_after": float(after[:, k].max())})
        print(f"limit {lim}: {runs[f'limit_{lim}']}", flush=True)
    sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                         text=True).stdout.strip()
    summary = {"commit_at_run": sha, "model": model, "redispatch": runs,
               "reference": {k: {"value": v, "source": s} for k, (v, s) in REF.items()}}
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    pd.DataFrame(monthly).round(1).to_csv(out_dir / "redispatch_by_month.csv")
    pd.DataFrame(unresolved_rows).sort_values(["limit", "hours"], ascending=[True, False]).to_csv(
        out_dir / "unresolved_branches.csv", index=False)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
