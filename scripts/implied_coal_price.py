"""Implied 2024 hard-coal fuel price from unit start/stop behaviour (input estimate, A29).

Method: for each ENTSO-E hard-coal unit with > 0.05 TWh in 2024, find start events (output
crosses 30% of its observed maximum upwards) and stop events (downwards). The mean day-ahead
price (SMARD DE-LU) over the 24 h after a start / before a stop approximates the price at which
the unit's marginal cost is covered. Implied fuel price per event:
    fuel = (p24 - VOM - CO2_month * EF * 0.0036 / eta) * eta
with eta, VOM, EF of hard_coal_sub (config plant_costs) and monthly EUA (prices 2024_validation).
Reported: median over units of the per-unit median, with interquartile range.
Writes results/inputs/implied_coal_price_2024.json. Not a calibration result.
"""

from __future__ import annotations

import json
import subprocess

import pandas as pd

from netzfix.config import DATA_PROCESSED, RESULTS, load_config


def main() -> None:
    cfg = load_config()
    tech = cfg["plant_costs"]["technologies"]["hard_coal_sub"]
    co2 = cfg["prices"]["sets"]["2024_validation"]["co2_eur_t"]
    u = pd.read_parquet(DATA_PROCESSED / "entsoe_units_DE_2024.parquet")
    meta = pd.read_csv(DATA_PROCESSED / "entsoe_units_DE_2024_meta.csv")
    hc = meta[(meta["type"] == "Fossil Hard coal") & (meta["twh"] > 0.05)]
    smard = pd.read_parquet(DATA_PROCESSED / "smard_DE_2024.parquet")
    price = smard["price_de_lu"].reindex(u.index)
    rows = []
    for r in hc.itertuples():
        on = u[r.code].fillna(0.0) > 0.3 * r.p_max_obs
        prev = on.shift(1, fill_value=False)
        for kind, ev in (("start", on & ~prev), ("stop", ~on & prev)):
            for t in ev[ev].index:
                w = (price.loc[t:t + pd.Timedelta(hours=23)] if kind == "start"
                     else price.loc[t - pd.Timedelta(hours=23):t])
                rows.append((r.code, kind, t.month, w.mean()))
    e = pd.DataFrame(rows, columns=["code", "kind", "month", "p24"]).dropna()
    eta, ef, vom = float(tech["eta"]), float(tech["ef_t_tj"]), float(tech["vom"])
    e["fuel"] = (e["p24"] - vom - e["month"].map(lambda m: co2[m - 1]) * ef * 0.0036 / eta) * eta
    unit = e.groupby("code")["fuel"].median()
    out = {
        "commit": subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                                 text=True).stdout.strip(),
        "units": int(unit.size), "events": {k: int(v) for k, v in e["kind"].value_counts().items()},
        "p24_median_eur_mwh": float(e["p24"].median()),
        "fuel_eur_mwh_th": {"median_of_unit_medians": float(unit.median()),
                            "q25": float(unit.quantile(0.25)), "q75": float(unit.quantile(0.75)),
                            "median_all_events": float(e["fuel"].median())},
        "assumptions": {"eta": eta, "ef_t_tj": ef, "vom": vom, "on_threshold": 0.3,
                        "window_h": 24},
    }
    d = RESULTS / "inputs"
    d.mkdir(parents=True, exist_ok=True)
    (d / "implied_coal_price_2024.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
