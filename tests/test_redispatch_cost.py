"""Toy network for the cost-based redispatch rule (A25), with hand-computed answers.

One monitored branch, limit 100 MW, pre-redispatch flow 110 MW (10 MW overload).
Buses: 0 = renewable plant in the north (PTDF 1.0), 1 = conventional plant in the north
(PTDF s_c), 2 = conventional plant in the south (PTDF 0.0, provides the upward MW), 3 = slack.
Prices 2023/24 (netztransparenz): c_up 222.00, c_down -142.23, p_ee 575.70.
  renewable pair  : curtail 10 MW at bus 0 + 10 MW up at bus 2 -> 10 * (222.00 + 575.70) = 7,977.0
  conventional pair: 10 / s_c MW down at bus 1 + same up at bus 2 -> (10 / s_c) * 79.77
  s_c = 0.05 -> 200 MW -> 15,954.0 > 7,977.0 -> curtail renewables (sensitivity ratio 20 > 10)
  s_c = 0.20 ->  50 MW ->  3,988.5 < 7,977.0 -> reduce conventional (ratio 5 < 10)
Minimum-volume rule picks the renewable in both cases (10 MW instead of 50 or 200 MW).
"""

import numpy as np
import pandas as pd
import pytest

from netzfix.config import load_config
from netzfix.sim.redispatch import CostRule, redispatch

PRICES = dict(c_up=222.00, c_down=-142.23, p_ee=575.70)


def _toy(s_c: float, costs: CostRule | None):
    ptdf = np.array([[1.0, s_c, 0.0, 0.0]])
    flow0 = np.array([[110.0]])
    s_nom = np.array([100.0])
    headroom = np.array([[0.0, 0.0, 500.0, 0.0]])
    disp = np.array([[0.0, 500.0, 0.0, 0.0]])
    res = np.array([[300.0, 0.0, 0.0, 0.0]])
    return redispatch(flow0, ptdf, s_nom, headroom, disp, res, limit_pu=1.0, costs=costs)


def _rule() -> CostRule:
    return CostRule(*(np.array([PRICES[k]]) for k in ("c_up", "c_down", "p_ee")))


def test_cost_rule_curtails_renewables_when_ten_times_more_effective():
    r = _toy(0.05, _rule())
    assert r.down_res[0, 0] == pytest.approx(10.0, abs=1e-6)
    assert r.down_disp.sum() == pytest.approx(0.0, abs=1e-6)
    assert r.up[0, 2] == pytest.approx(10.0, abs=1e-6)
    assert r.cost_eur[0] == pytest.approx(7_977.0, abs=1e-3)
    assert r.flow[0, 0] == pytest.approx(100.0, abs=1e-6)


def test_cost_rule_reduces_conventional_when_less_than_ten_times():
    r = _toy(0.20, _rule())
    assert r.down_res.sum() == pytest.approx(0.0, abs=1e-6)
    assert r.down_disp[0, 1] == pytest.approx(50.0, abs=1e-6)
    assert r.up[0, 2] == pytest.approx(50.0, abs=1e-6)
    assert r.cost_eur[0] == pytest.approx(3_988.5, abs=1e-3)


def test_min_volume_rule_always_curtails_renewables_here():
    r = _toy(0.20, None)
    assert r.down_res[0, 0] == pytest.approx(10.0, abs=1e-6)
    assert r.down_disp.sum() == pytest.approx(0.0, abs=1e-6)


def test_prices_switch_on_first_october_local_time():
    periods = load_config()["redispatch"]["prices"]
    idx = pd.DatetimeIndex(["2024-09-30 21:00", "2024-09-30 22:00"], tz="UTC")  # 23:00 / 00:00 CEST
    c = CostRule.from_config(idx, periods)
    assert c.c_up.tolist() == [222.00, 181.10]
    assert c.p_ee.tolist() == [575.70, 325.8]


def test_config_prices_follow_the_minimum_factor_formula():
    cfg = load_config()["redispatch"]
    mf = cfg["mindestfaktor_ee"]
    for r in cfg["prices"]:   # p_ee = MF * (c_up + c_down) - c_up, published to 0.1 EUR/MWh
        assert r["p_ee"] == pytest.approx(mf * (r["c_up"] + r["c_down"]) - r["c_up"], abs=0.15)
