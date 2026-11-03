"""Calibrate the line margin and evaluate the pre-registered tests.

Usage:
  uv run python scripts/calibration_report.py              # grid runs -> alpha* (interpolated)
  uv run python scripts/calibration_report.py --test 0.83  # evaluate tests on the run at alpha*
Reads results/calibration/alpha_*.json; writes results/calibration/report.json.

Reference values: SMARD article "Volumen und Kosten gesunken" (Bundesnetzagentur, 2025-04-02),
held in vault/literature/pdfs/ as
SMARD_2025-04-02_Netzengpassmanagement_2024_Volumen_und_Kosten_gesunken.html.
Target and tests are pre-registered in vault/project/Validation.md.
"""

from __future__ import annotations

import argparse
import json
import pathlib

import numpy as np

from netzfix.config import RESULTS

DIR = RESULTS / "calibration"
# --- reference values (GWh, 2024) --------------------------------------------------------
MARKET_REDISPATCH = 22_777     # adjusted feed-in of market plants (= 14,454 down + 8,322 up)
RESERVE = 1_788                # reserve plants
TARGET = MARKET_REDISPATCH + RESERVE   # 24,565: our model has no countertrading (5,739)
CURTAIL_RES = 9_374            # redispatch with renewables
CURTAIL_MIX = {"wind_offshore": 4_562, "wind_onshore": 3_384, "solar": 1_389}
DOWN_TOTAL = 14_454            # reductions of market plants (renewables + conventional)
Q4_TOTAL, YEAR_TOTAL = 10_424, 30_304
UP_TOP2 = {"gas", "hard_coal"}  # gas 4,151 and hard coal 3,792 GWh most increased


def load(d=DIR) -> dict[float, dict]:
    runs = {}
    for f in sorted(d.glob("alpha_*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        runs[d["alpha"]] = d
    return runs


def alpha_star(runs: dict[float, dict]) -> float:
    a = np.array(sorted(runs))
    v = np.array([runs[x]["gwh"]["up_plus_down"] for x in a])
    if not (v.min() <= TARGET <= v.max()):
        raise ValueError(f"target {TARGET} outside the grid range {v.min():.0f}-{v.max():.0f}")
    order = np.argsort(v)                        # volume falls with alpha; interpolate on volume
    return float(np.interp(TARGET, v[order], a[order]))


def tests(d: dict) -> dict:
    g = d["gwh"]
    cur = d["curtail_by_carrier_gwh"]
    cur_mix_total = sum(cur.get(c, 0.0) for c in CURTAIL_MIX)
    res = {}
    res["T0_calibration_volume"] = {"model": g["up_plus_down"], "real": TARGET}
    res["T1_curtailment_total"] = {
        "model": g["down_curtail"], "real": CURTAIL_RES,
        "pass": 0.65 * CURTAIL_RES <= g["down_curtail"] <= 1.35 * CURTAIL_RES}
    mix = {}
    real_mix_total = sum(CURTAIL_MIX.values())
    for c, real in CURTAIL_MIX.items():
        ms = cur.get(c, 0.0) / cur_mix_total if cur_mix_total else 0.0
        rs = real / real_mix_total
        mix[c] = {"model_share": ms, "real_share": rs, "pass": abs(ms - rs) <= 0.15}
    res["T2_curtailment_mix"] = {"by_carrier": mix, "pass": all(x["pass"] for x in mix.values())}
    q4 = d["quarter_gwh"]["4"] if "4" in d["quarter_gwh"] else d["quarter_gwh"][4]
    q4s = q4 / g["up_plus_down"]
    res["T3_q4_share"] = {"model": q4s, "real": Q4_TOTAL / YEAR_TOTAL,
                          "pass": abs(q4s - Q4_TOTAL / YEAR_TOTAL) <= 0.10}
    up = d["up_by_carrier_gwh"]
    top2 = set(sorted(up, key=up.get, reverse=True)[:2])
    res["T4_up_top2"] = {"model": sorted(up.items(), key=lambda x: -x[1]), "real": sorted(UP_TOP2),
                         "pass": top2 == UP_TOP2}
    down = g["down_curtail"] + g["down_dispatchable"]
    rs = CURTAIL_RES / DOWN_TOTAL
    ms = g["down_curtail"] / down if down else 0.0
    res["T5_res_share_of_down"] = {"model": ms, "real": rs, "pass": abs(ms - rs) <= 0.15}
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", type=float, default=None, help="alpha of the run to test")
    ap.add_argument("--dir", default=str(DIR), help="folder with alpha_*.json")
    a = ap.parse_args()
    d = pathlib.Path(a.dir)
    runs = load(d)
    report = {"target_gwh": TARGET,
              "grid": {str(k): {"up_plus_down_gwh": v["gwh"]["up_plus_down"],
                                "unresolved_gwh": v["unresolved_gwh"]} for k, v in runs.items()},
              "alpha_star": alpha_star(runs)}
    if a.test is not None:
        report["tested_alpha"] = a.test
        report["tests"] = tests(runs[a.test])
    (d / "report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
