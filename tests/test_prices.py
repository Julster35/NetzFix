"""A29/A30: price layer and marginal cost (hand-computed)."""

import numpy as np
import pandas as pd
import pytest

from netzfix.config import load_config
from netzfix.markets.prices import MissingPrice, marginal_cost, parse_dehst_average, price_table

IDX = pd.DatetimeIndex(["2024-01-15 12:00", "2024-12-15 12:00"], tz="UTC")


def test_validation_prices_monthly_co2_and_flat_gas():
    p = price_table(IDX, "2024_validation")
    assert p["co2"].tolist() == [61.94, 66.66]          # DEHSt Jan / Dec 2024
    assert p["gas"].tolist() == [34.64, 34.64]          # EGSI annual average
    assert p["hard_coal"].tolist() == [8.3, 8.3]        # implied from unit starts/stops
    assert p["oil"].isna().all()                        # not held


def test_missing_required_price_raises():
    with pytest.raises(MissingPrice):
        price_table(IDX, "2024_validation", required=("oil",))


def test_gas_cc_marginal_cost_hand_computed():
    # 34.64/0.605 = 57.25620; 65 * 55.8 * 0.0036 / 0.605 = 21.58215; + VOM 4 -> 82.83835
    tech = load_config()["plant_costs"]["technologies"]["gas_cc"]
    prices = pd.DataFrame({"gas": [34.64], "co2": [65.0]})
    assert marginal_cost(tech, prices)[0] == pytest.approx(82.83835, abs=1e-4)


def test_user_price_set_overrides():
    cfg = load_config()
    cfg["prices"]["sets"]["user"] = {"co2_eur_t": 120.0, "gas_eur_mwh_th": 40.0,
                                     "hard_coal_eur_mwh_th": 12.0}
    p = price_table(IDX, "user", cfg=cfg)
    assert np.allclose(p[["co2", "gas", "hard_coal"]].to_numpy(), [[120, 40, 12]] * 2)


def test_parse_dehst_average_from_report_sentence():
    # sentence as in the held DEHSt Q4 2024 report, PDF p. 3
    s = "This results in a volume-weighted average price per allowance of € 65,52 (minus 3 percent"
    assert parse_dehst_average(s) == 65.52


def test_parse_dehst_average_monthly_report_wording():
    # wording of the monthly reports (DEHSt August 2026, PDF p. 5), line break inside
    s = "This results in a  " + chr(10) + "volume-weighted average price per allowance of €82.31"
    assert parse_dehst_average(s) == 82.31
