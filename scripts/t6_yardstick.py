"""T6: model redispatch vs the TSOs' published 2024 redispatch measures (pre-registered in
vault/project/Validation.md, "T6 (yardstick ...): PRE-REGISTRATION", 2026-11-05).

Real data: data/raw/netztransparenz/redispatch/redispatch_2024_MM_UTC.csv
(src/netzfix/data/netztransparenz_redispatch.py). Model: default config (v8) at --alpha, same
redispatch call as scripts/calibrate_margin.py. Writes <out>/t6.json.

  uv run python scripts/t6_yardstick.py --alpha 0.997 --out results/calibration_v8
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from netzfix.config import DATA_RAW, REPO_ROOT, load_config
from netzfix.data.entsoe_units import _asset_area
from netzfix.server.state import Playground
from netzfix.sim.behaviours import Context
from netzfix.sim.redispatch import CostRule, redispatch

REASONS = {"Strombedingter Redispatch", "Strom- und Spannungsbedingter RD"}
TSO_NAME = {"DE_50HzT": "50Hertz", "DE_Amprion": "Amprion", "DE_TenneT_GER": "TenneT DE",
            "DE_TransnetBW": "TransnetBW"}
TVD_MAX, RHO_MIN, TSO_TOL = 0.15, 0.50, 0.10          # frozen in the pre-registration


def real(year: int = 2024) -> pd.DataFrame:
    raw = DATA_RAW / "netztransparenz" / "redispatch"
    files = sorted(raw.glob(f"redispatch_{year}_*_UTC.csv"))
    if len(files) != 12:
        raise FileNotFoundError(f"expected 12 monthly files, found {len(files)}")
    d = pd.concat([pd.read_csv(f, sep=";", decimal=",", encoding="utf-8-sig") for f in files])
    d = d.drop_duplicates()
    sel = d[d.GRUND_DER_MASSNAHME.isin(REASONS) & (d.BETROFFENE_ANLAGE != "Börse")].copy()
    t0 = pd.to_datetime(sel.BEGINN_DATUM + " " + sel.BEGINN_UHRZEIT, format="%d.%m.%Y %H:%M",
                        utc=True)
    t1 = pd.to_datetime(sel.ENDE_DATUM + " " + sel.ENDE_UHRZEIT, format="%d.%m.%Y %H:%M", utc=True)
    mid = (t0 + (t1 - t0) / 2).dt.tz_convert("Europe/Berlin")
    sel["day"] = mid.dt.normalize().dt.tz_localize(None)
    sel = sel[sel.day.dt.year == year]
    sel["mwh"] = sel.GESAMTE_ARBEIT_MWH.astype(float)
    sel["down"] = sel.RICHTUNG.str.contains("reduzieren")
    return sel


def model(alpha: float) -> tuple[pd.Series, pd.Series, float]:
    """Daily volume (GWh, Berlin date) and volume by TSO (GWh); unmapped volume (GWh)."""
    rcfg = load_config()["redispatch"]
    pg = Playground()
    ctx = Context(ts=pg.ts, capacity=pg.capacity, regional_cf=pg.regional_cf)
    r = pg.simulate(ctx, track_carriers=True)
    costs = (CostRule.from_config(pg.ts.index, rcfg["prices"])
             if rcfg["rule"] == "cost_based" else None)
    down = r.down_bus if r.down_bus is not None else r.disp_bus
    reserve = r.reserve_bus if (r.reserve_bus is not None and r.reserve_bus.any()) else None
    rd = redispatch(r.flow, pg.ptdf, pg.s_nom, r.headroom_bus, down, r.res_bus,
                    limit_pu=alpha, costs=costs, reserve=reserve)
    ur = rd.up_reserve if rd.up_reserve is not None else np.zeros_like(rd.up)
    vol = rd.up + ur + rd.down_disp + rd.down_res                    # T x buses, MWh
    days = pg.ts.index.tz_convert("Europe/Berlin").normalize().tz_localize(None)
    daily = pd.Series(vol.sum(axis=1), index=days).groupby(level=0).sum() / 1e3
    b = pg.grid.network.buses.reindex(pg.buses)
    assets = pd.DataFrame({"id": np.arange(len(pg.buses)), "lon": b.x.to_numpy(),
                           "lat": b.y.to_numpy()})
    area = _asset_area(assets, load_config()["entsoe_units"]["tso_by_nuts1"])
    per_bus = pd.Series(vol.sum(axis=0) / 1e3)
    tso = per_bus.groupby(area.reindex(per_bus.index).map(TSO_NAME)).sum()
    unmapped = float(per_bus[area.reindex(per_bus.index).isna().to_numpy()].sum())
    return daily, tso, unmapped


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--alpha", type=float, required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    R = real()
    r_day = R.groupby("day").mwh.sum() / 1e3
    m_day, m_tso, unmapped = model(a.alpha)
    idx = pd.date_range("2024-01-01", "2024-12-31", freq="D")
    r_day, m_day = r_day.reindex(idx, fill_value=0.0), m_day.reindex(idx, fill_value=0.0)

    r_mon, m_mon = r_day.groupby(idx.month).sum(), m_day.groupby(idx.month).sum()
    r_ms, m_ms = r_mon / r_mon.sum(), m_mon / m_mon.sum()
    tvd = 0.5 * float((r_ms - m_ms).abs().sum())
    rho = float(spearmanr(m_day, r_day).statistic)
    r_tso = R.groupby("ANWEISENDER_UENB").mwh.sum() / 1e3
    r_ts, m_ts = r_tso / r_tso.sum(), m_tso / m_tso.sum()
    tso_rows = {t: {"model_share": float(m_ts.get(t, 0.0)), "real_share": float(r_ts.get(t, 0.0)),
                    "pass": bool(abs(m_ts.get(t, 0.0) - r_ts.get(t, 0.0)) <= TSO_TOL)}
                for t in TSO_NAME.values()}
    down_ee = R[R.down & (R.PRIMAERENERGIEART == "Erneuerbar")]
    off = down_ee[down_ee.BETROFFENE_ANLAGE.str.startswith("OWP")].mwh.sum()

    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                            text=True, cwd=REPO_ROOT).stdout.strip()
    res = {
        "alpha": a.alpha, "commit_at_run": commit,
        "real_selected_rows": int(len(R)), "real_total_gwh": float(r_day.sum()),
        "model_total_gwh": float(m_day.sum()), "model_unmapped_gwh": unmapped,
        "monthly_gwh": {"model": m_mon.round(1).tolist(), "real": r_mon.round(1).tolist()},
        "T6a_monthly_tvd": {"value": tvd, "max": TVD_MAX, "pass": bool(tvd <= TVD_MAX)},
        "T6b_daily_spearman": {"value": rho, "min": RHO_MIN, "pass": bool(rho >= RHO_MIN)},
        "T6c_tso_share": {"by_tso": tso_rows, "pass": all(x["pass"] for x in tso_rows.values())},
        "T6d_offshore_share_of_res_down": {
            "value": float(off / down_ee.mwh.sum()), "owp_gwh": float(off) / 1e3,
            "res_down_gwh": float(down_ee.mwh.sum()) / 1e3},
    }
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "t6.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    pd.DataFrame({"model_gwh": m_day, "real_gwh": r_day}).to_csv(out / "t6_daily.csv",
                                                                 index_label="day")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
