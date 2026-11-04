"""One calibration run: full year 2024 + redispatch at line margin `alpha` (limit = alpha * s_nom).

Usage: uv run python scripts/calibrate_margin.py --alpha 0.85 [--out results/calibration]
                                                  [--rule cost_based|min_volume]
The rule defaults to `redispatch.rule` in config/default.yaml (A25).
Writes <out>/alpha_<alpha>.json with total volumes, volumes by technology and by quarter.
Pre-registration of target and tests: vault/project/Validation.md ("Calibration of the line
margin", written before any calibration run).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path

import numpy as np

from netzfix.config import RESULTS, load_config
from netzfix.server.state import Playground
from netzfix.sim.behaviours import Context
from netzfix.sim.redispatch import CostRule, redispatch


def attribute(vol: np.ndarray, total: np.ndarray, parts: dict[str, np.ndarray]) -> dict:
    """Split a T x buses volume over carriers in proportion to their per-bus share of `total`."""
    with np.errstate(divide="ignore", invalid="ignore"):
        return {c: float(np.nansum(np.where(total > 1e-9, vol * x / total, 0.0)) / 1e3)
                for c, x in parts.items()}                           # GWh


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--alpha", type=float, required=True)
    ap.add_argument("--out", default=str(RESULTS / "calibration"))
    ap.add_argument("--rule", choices=("cost_based", "min_volume"), default=None)
    a = ap.parse_args()
    rcfg = load_config()["redispatch"]
    rule = a.rule or rcfg["rule"]
    t0 = time.time()
    pg = Playground()
    ctx = Context(ts=pg.ts, capacity=pg.capacity, regional_cf=pg.regional_cf)
    r = pg.simulate(ctx, track_carriers=True)
    costs = CostRule.from_config(pg.ts.index, rcfg["prices"]) if rule == "cost_based" else None
    down = r.down_bus if r.down_bus is not None else r.disp_bus     # A31 minimum load
    rd = redispatch(r.flow, pg.ptdf, pg.s_nom, r.headroom_bus, down, r.res_bus,
                    limit_pu=a.alpha, costs=costs)
    q = pg.ts.index.tz_convert("Europe/Berlin").quarter.to_numpy()
    tot = (rd.up + rd.down_disp + rd.down_res).sum(axis=1)
    out = {
        "alpha": a.alpha,
        "rule": rule,
        "commit_at_run": subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                                        capture_output=True, text=True).stdout.strip(),
        "seconds": round(time.time() - t0, 1),
        "gwh": {"up": rd.up.sum() / 1e3, "down_dispatchable": rd.down_disp.sum() / 1e3,
                "down_curtail": rd.down_res.sum() / 1e3, "up_plus_down": tot.sum() / 1e3},
        "unresolved_gwh": float(rd.unresolved.sum() / 1e3),
        "hours_unresolved": int((rd.unresolved > 0.5).sum()),
        "selection_cost_meur": (float(rd.cost_eur.sum() / 1e6) if rd.cost_eur is not None
                                else None),
        "quarter_gwh": {int(k): float(tot[q == k].sum() / 1e3) for k in (1, 2, 3, 4)},
        "curtail_by_carrier_gwh": attribute(rd.down_res, r.res_bus, r.res_by_carrier),
        "up_by_carrier_gwh": attribute(rd.up, r.headroom_bus, r.headroom_by_carrier),
        "down_disp_by_carrier_gwh": attribute(rd.down_disp, down,
                                              r.down_by_carrier or r.disp_by_carrier),
        "min_load_units": pg.min_load_units,
    }
    d = Path(a.out)
    d.mkdir(parents=True, exist_ok=True)
    (d / f"alpha_{a.alpha:.3f}.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
