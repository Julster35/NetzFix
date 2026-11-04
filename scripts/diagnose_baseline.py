"""Diagnostics of the 2024 'as is' playground baseline (no edits), full year.

Usage: uv run python scripts/diagnose_baseline.py
Writes results/playground_baseline_2024/diagnostics.json. Descriptive check of the playground,
not a market-design result (no Analysis Log entry needed, see Decision Log 2026-11-03 "Re-scope").
"""

from __future__ import annotations

import json
import subprocess

import numpy as np

from netzfix.config import RESULTS
from netzfix.server.state import Playground
from netzfix.sim.behaviours import Context

CARRIERS = ["solar", "wind_onshore", "wind_offshore", "biomass", "hydro", "lignite", "hard_coal",
            "gas", "other_conventional", "other_renewable"]


def main() -> None:
    pg = Playground()
    n = pg.grid.network
    ts = pg.ts
    ctx = Context(ts=ts, capacity=pg.capacity, regional_cf=pg.regional_cf)
    r = pg.simulate(ctx)
    L = r.loading
    mx = L.max(axis=0)
    top = []
    for k in np.argsort(mx)[::-1][:10]:
        comp, bid = pg.branches[k].split(":", 1)
        df = n.lines if comp == "Line" else n.transformers
        v_kv = float(n.buses.at[df.at[bid, "bus0"], "v_nom"])
        top.append({"branch": pg.branches[k], "v_kv": v_kv,
                    "s_nom": round(float(pg.s_nom[k]), 1), "max_loading": round(float(mx[k]), 3),
                    "hours_over_100pct": int((L[:, k] > 1).sum())})
    clipped = {}
    for c in CARRIERS:
        cap = ctx.by_month(pg.capacity[c])
        clipped[c] = {"max_cf": round(float((ts[c].to_numpy() / cap).max()), 3),
                      "clipped_gwh": round(float(np.clip(ts[c].to_numpy() - cap, 0, None).sum()
                                                 / 1e3), 1)}
    sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                         text=True).stdout.strip()
    out = {
        "commit_at_run": sha, "hours": len(ts), "branches": len(pg.branches),
        "buses": len(pg.buses), "assets": len(pg.assets()),
        "line_hours_over_70pct": int((L > 0.7).sum()),
        "line_hours_over_100pct": int((L > 1).sum()),
        "share_line_hours_over_100pct": round(float((L > 1).mean()), 5),
        "branches_ever_over_100pct": int((mx > 1).sum()),
        "max_trade_deviation_mw": round(float(np.abs(r.trade_deviation).max()), 6),
        "energy_twh": {c: round(float(v.sum()) / 1e6, 2) for c, v in r.by_carrier.items()},
        "smard_energy_twh": {c: round(float(ts[c].sum()) / 1e6, 2) for c in CARRIERS + ["load"]},
        "capacity_factor_check": clipped,
        "top_branches": top,
    }
    d = RESULTS / "playground_baseline_2024"
    d.mkdir(parents=True, exist_ok=True)
    (d / "diagnostics.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k not in ("top_branches",)}, indent=1))


if __name__ == "__main__":
    main()
