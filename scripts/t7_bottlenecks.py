"""T7: where is the grid congested? Model v8 vs the BNetzA lists of overloaded elements.

Pre-registered in vault/project/Validation.md ("T7 ... PRE-REGISTRATION", 2026-11-06).

Real (R): data/processed/bnetza_overloaded_elements.csv (src/netzfix/data/bnetza_congestion.py),
hours of overload per element and quarter from the TSOs' operational planning (PRD1), top 20-25
elements per quarter; an element not listed in a quarter counts 0 there (it is below the cut).
Model (M): v8 market flows before redispatch (same simulate call as scripts/calibrate_margin.py);
a branch-hour is overloaded if |flow| > alpha * s_nom. Element hours = sum over the element's
matched branches (src/netzfix/network/element_match.py, A36) of overloaded hours.

Periods: T7a = R Q1+Q2 2024 vs M Jan-Jun 2024 (Europe/Berlin quarters 1-2).
         T7b = R Q1-Q4 2023 vs M full 2024 (cross-year; the 2024 Q3/Q4 lists are not published).
Tests per period, over matched elements listed in that period:
  rho   Spearman rank correlation R vs M hours            pass if >= 0.50
  top5  of R's top-5 elements, how many are in M's top-5  pass if >= 3
T7c (descriptive): share of M's overloaded branch-hours (whole year, all branches) that lie on a
matched listed element; M's 15 most overloaded branches with location and element (if any).

Usage: uv run python scripts/t7_bottlenecks.py --alpha 0.997 --out results/calibration_v8
       (--match-only writes the match report and stops before any flow is computed)
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from netzfix.config import DATA_PROCESSED, REPO_ROOT
from netzfix.network.element_match import element_of_name, key, match
from netzfix.server.state import Playground
from netzfix.sim.behaviours import Context

RHO_MIN = 0.50
TOP_K = 5
TOP_HITS_MIN = 3


def real_hours() -> pd.DataFrame:
    d = pd.read_csv(DATA_PROCESSED / "bnetza_overloaded_elements.csv", encoding="utf-8")
    m = element_of_name()
    d["element_id"] = d.element.map(lambda x: m.get(key(x)))
    if d.element_id.isna().any():
        raise ValueError(f"names without config entry: {sorted(d.element[d.element_id.isna()])}")
    return d


def period_test(r: pd.Series, m: pd.Series) -> dict:
    df = pd.DataFrame({"real_h": r, "model_h": m}).dropna()
    rho = float(spearmanr(df.real_h, df.model_h).statistic) if len(df) > 2 else float("nan")
    top_r = list(df.real_h.sort_values(ascending=False).index[:TOP_K])
    top_m = list(df.model_h.sort_values(ascending=False).index[:TOP_K])
    hits = len(set(top_r) & set(top_m))
    return {"n_elements": int(len(df)), "spearman": rho, "pass_rho": bool(rho >= RHO_MIN),
            "top_real": top_r, "top_model": top_m, "top_hits": hits,
            "pass_top": bool(hits >= TOP_HITS_MIN),
            "table": df.sort_values("real_h", ascending=False).reset_index(names="element")
                       .to_dict("records")}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--alpha", type=float, default=0.997)
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "results" / "calibration_v8")
    ap.add_argument("--match-only", action="store_true")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)

    pg = Playground()
    n = pg.grid.network
    elements, report = match(n, list(pg.branches))
    report.to_csv(a.out / "t7_match_report.csv", index=False, encoding="utf-8")
    (a.out / "t7_match.json").write_text(json.dumps(elements, indent=1), encoding="utf-8")
    R = real_hours()
    print(f"{len(elements)} elements matched; listed elements without match: "
          f"{sorted(set(R.element_id) - set(elements))}")
    if a.match_only:
        return

    ctx = Context(ts=pg.ts, capacity=pg.capacity, regional_cf=pg.regional_cf)
    r = pg.simulate(ctx)
    over = np.abs(r.flow) > a.alpha * pg.s_nom + 1e-6                 # T x branches
    q = pg.ts.index.tz_convert("Europe/Berlin").quarter.to_numpy()
    bidx = {b: k for k, b in enumerate(pg.branches)}
    h_all = over.sum(axis=0)
    h_h1 = over[q <= 2].sum(axis=0)

    def el_hours(h: np.ndarray) -> pd.Series:
        return pd.Series({e: float(h[[bidx[b] for b in brs]].sum()) for e, brs in elements.items()})

    m_h1, m_y = el_hours(h_h1), el_hours(h_all)
    R = R[R.element_id.isin(elements)]
    r24 = R[(R.year == 2024) & (R.quarter <= 2)].groupby("element_id").hours.sum()
    r23 = R[R.year == 2023].groupby("element_id").hours.sum()
    t7a = period_test(r24, m_h1.reindex(r24.index))
    t7b = period_test(r23, m_y.reindex(r23.index))

    on_el = np.zeros(len(pg.branches), bool)
    el_of = {}
    for e, brs in elements.items():
        for b in brs:
            on_el[bidx[b]] = True
            el_of.setdefault(b, []).append(e)
    listed = set(r24.index) | set(r23.index)
    on_listed = np.array([any(e in listed for e in el_of.get(b, [])) for b in pg.branches])
    top = np.argsort(-h_all)[:15]
    tops = []
    for k in top:
        comp, idx = pg.branches[k].split(":", 1)
        tab = n.lines if comp == "Line" else n.transformers
        b0, b1 = tab.at[idx, "bus0"], tab.at[idx, "bus1"]
        tops.append({"branch": pg.branches[k], "hours_over": int(h_all[k]),
                     "v_nom": float(n.buses.at[b0, "v_nom"]), "s_nom": float(pg.s_nom[k]),
                     "lat": float((n.buses.at[b0, "y"] + n.buses.at[b1, "y"]) / 2),
                     "lon": float((n.buses.at[b0, "x"] + n.buses.at[b1, "x"]) / 2),
                     "element": el_of.get(pg.branches[k], [])})
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                            text=True, cwd=REPO_ROOT).stdout.strip()
    out = {"alpha": a.alpha, "commit_at_run": commit,
           "thresholds": {"rho_min": RHO_MIN, "top_k": TOP_K, "top_hits_min": TOP_HITS_MIN},
           "n_elements_matched": len(elements),
           "T7a_H1_2024": t7a, "T7b_2023_vs_model_2024": t7b,
           "T7c": {"branch_hours_over_total": int(h_all.sum()),
                   "share_on_listed_elements": float(h_all[on_listed].sum() / max(h_all.sum(), 1)),
                   "share_on_any_matched_element": float(h_all[on_el].sum() / max(h_all.sum(), 1)),
                   "n_branches_on_listed": int(on_listed.sum()),
                   "top15_model_branches": tops}}
    (a.out / "t7.json").write_text(json.dumps(out, indent=1, ensure_ascii=False),
                                   encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "T7c"} | {
        "T7c_share_on_listed": out["T7c"]["share_on_listed_elements"]}, indent=1,
        ensure_ascii=False, default=str)[:6000])


if __name__ == "__main__":
    main()
