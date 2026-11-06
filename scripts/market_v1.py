"""Market v1 (A39): uniform merit-order price and thermal mix vs SMARD (checks V1, V2).

Pre-registered in vault/project/Validation.md ("Market v1 ... PRE-REGISTRATION of V1/V2").
Usage: uv run python scripts/market_v1.py --year 2024 [--hours N]
Writes results/market_v1/<year>.json and <year>_hourly.csv.
"""

from __future__ import annotations

import argparse
import json
import subprocess

import numpy as np
import pandas as pd

from netzfix.config import REPO_ROOT, RESULTS
from netzfix.markets.dispatch import THERMAL, run
from netzfix.server.state import Playground


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2024)
    ap.add_argument("--hours", type=int, default=None, help="smoke test: first N hours")
    a = ap.parse_args()
    pg = Playground()
    ts = pg.ts if a.hours is None else pg.ts.iloc[: a.hours]
    res, fl = run(pg.assets(), ts)
    real = ts["price_de_lu"].to_numpy(dtype=float)
    ok = ~np.isnan(res.price) & ~np.isnan(real)
    r = float(np.corrcoef(res.price[ok], real[ok])[0, 1])
    pos = ok & (real > 0)
    r_pos = float(np.corrcoef(res.price[pos], real[pos])[0, 1])
    mean_m, mean_r = float(np.nanmean(res.price[ok])), float(np.nanmean(real[ok]))
    mix_m = {c: float(res.gen[:, (fl.carrier == c).to_numpy()].sum() / 1e6) for c in THERMAL}
    mix_r = {c: float(ts[c].sum() / 1e6) for c in THERMAL}
    v2 = {c: {"model_twh": mix_m[c], "real_twh": mix_r[c],
              "pass": bool(abs(mix_m[c] - mix_r[c]) <= max(0.2 * mix_r[c], 5.0))}
          for c in THERMAL}
    out = {
        "year": a.year, "hours": int(len(ts)),
        "commit_at_run": subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                                        capture_output=True, text=True,
                                        cwd=REPO_ROOT).stdout.strip(),
        "units": int(len(fl)), "fleet_mw_by_technology":
            {t: float(np.mean([p.mean() for p in g.p_nom_m])) * len(g)
             for t, g in fl.groupby("technology")},
        "V1": {"pearson_r": r, "pass_r": bool(r >= 0.8), "mean_model": mean_m,
               "mean_real": mean_r, "pass_mean": bool(abs(mean_m / mean_r - 1) <= 0.15),
               "mae": float(np.mean(np.abs(res.price[ok] - real[ok]))),
               "pearson_r_real_price_positive": r_pos, "hours_compared": int(ok.sum()),
               "real_hours_price_le_0": int((real <= 0).sum())},
        "V2": v2,
        "shortfall_hours": int((res.shortfall > 0).sum()),
        "shortfall_gwh": float(res.shortfall.sum() / 1e3),
    }
    d = RESULTS / "market_v1"
    d.mkdir(parents=True, exist_ok=True)
    stem = f"{a.year}" + (f"_smoke{a.hours}h" if a.hours else "")
    (d / f"{stem}.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    pd.DataFrame({"price_model": res.price, "price_real": real,
                  "shortfall_mw": res.shortfall}, index=ts.index).to_csv(d / f"{stem}_hourly.csv")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
