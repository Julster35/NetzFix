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


def _toy(s_c: float, costs: CostRule | None, s_r: float = 1.0, cap: float = 500.0):
    ptdf = np.array([[s_r, s_c, 0.0, 0.0]])
    flow0 = np.array([[110.0]])
    s_nom = np.array([100.0])
    headroom = np.array([[0.0, 0.0, cap, 0.0]])
    disp = np.array([[0.0, cap, 0.0, 0.0]])
    res = np.array([[cap, 0.0, 0.0, 0.0]])
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


def test_cost_rule_resolves_overload_even_when_relief_is_expensive():
    """Weak sensitivities: relieving 1 MW costs more than 1e4 EUR, but security is mandatory.
    RE at PTDF 0.04: 250 MW pair -> 250 * 797.70 = 199,425; conventional at PTDF 0.005:
    2,000 MW pair -> 2,000 * 79.77 = 159,540 (15,954 EUR per MW of overload, above the old
    1e4 penalty) -> conventional, overload fully removed."""
    r = _toy(0.005, _rule(), s_r=0.04, cap=3_000.0)
    assert r.unresolved[0] == pytest.approx(0.0, abs=1e-6)
    assert r.flow[0, 0] == pytest.approx(100.0, abs=1e-4)
    assert r.down_disp[0, 1] == pytest.approx(2_000.0, abs=1e-3)
    assert r.down_res.sum() == pytest.approx(0.0, abs=1e-6)
    assert r.cost_eur[0] == pytest.approx(159_540.0, abs=0.5)


def _toy_reserve(market_headroom: float):
    """Bus 0 conventional down (PTDF 1), bus 1 market up (PTDF 0), bus 2 reserve up (PTDF 0).
    10 MW overload. Market pair 10 * (222.00 - 142.23) = 797.7; reserve pair
    10 * (476.50 - 142.23) = 3,342.7 -> market up first, reserve only without market headroom."""
    ptdf = np.array([[1.0, 0.0, 0.0, 0.0]])
    rule = CostRule(np.array([222.00]), np.array([-142.23]), np.array([575.70]),
                    np.array([476.50]))
    return redispatch(np.array([[110.0]]), ptdf, np.array([100.0]),
                      headroom=np.array([[0.0, market_headroom, 0.0, 0.0]]),
                      disp=np.array([[50.0, 0.0, 0.0, 0.0]]), res=np.zeros((1, 4)),
                      limit_pu=1.0, costs=rule, reserve=np.array([[0.0, 0.0, 50.0, 0.0]]))


def test_reserve_used_only_after_market_plants():
    r = _toy_reserve(50.0)
    assert r.up[0, 1] == pytest.approx(10.0, abs=1e-6)
    assert r.up_reserve.sum() == pytest.approx(0.0, abs=1e-6)
    assert r.cost_eur[0] == pytest.approx(797.7, abs=1e-3)
    r = _toy_reserve(0.0)
    assert r.up_reserve[0, 2] == pytest.approx(10.0, abs=1e-6)
    assert r.cost_eur[0] == pytest.approx(3342.7, abs=1e-3)
