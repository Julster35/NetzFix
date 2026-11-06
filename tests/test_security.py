"""A38: n-1 security in the redispatch LP, on a 3-bus triangle with a hand-computed answer.

Buses 1, 2, 3; lines 12, 13, 23 with equal reactance; slack bus 3. PTDF (injection at bus i,
withdrawal at bus 3):  bus 1 -> f12 1/3, f13 2/3, f23 1/3;  bus 2 -> f12 -1/3, f13 1/3, f23 2/3.
90 MW from bus 1 to a load at bus 3: base flows 30 / 60 / 30.
Shifting x MW of generation from bus 1 to bus 2 gives f12 = 30 - 2x/3, f13 = 60 - x/3,
f23 = 30 + x/3. Post-fault flows by hand:
  outage 13: f12' = 90 - x, f23' = 90;   outage 12: f13' = 90 - x, f23' = x;
  outage 23: f12' = -x,     f13' = 90.
Ratings 100 / 150 / 150, base limit 100%, post-fault limit 80% (80 / 120 / 120 MW):
the only binding constraint is f12' = 90 - x <= 80 after outage 13  ->  x = 10.
So the cheapest secure redispatch is: 10 MW up at bus 2, 10 MW down at bus 1.
"""

import numpy as np

from netzfix.sim.redispatch import CostRule, Security, lodf_matrix, redispatch

PTDF = np.array([[1 / 3, -1 / 3, 0.0],
                 [2 / 3, 1 / 3, 0.0],
                 [1 / 3, 2 / 3, 0.0]])
INC = np.array([[1, -1, 0],      # line 12
                [1, 0, -1],      # line 13
                [0, 1, -1]], dtype=float)
S_NOM = np.array([100.0, 150.0, 150.0])


def _costs(T=1):
    return CostRule(np.full(T, 100.0), np.full(T, -50.0), np.full(T, 1000.0), None)


def test_lodf_by_hand():
    lodf, valid, _ = lodf_matrix(PTDF, INC)
    assert valid.all()
    # outage of 12: f13' = f13 + f12, f23' = f23 - f12
    np.testing.assert_allclose(lodf[:, 0], [-1.0, 1.0, -1.0])
    # outage of 13: f12' = f12 + f13, f23' = f23 + f13
    np.testing.assert_allclose(lodf[:, 1], [1.0, -1.0, 1.0])


def test_bridge_outage_is_invalid():
    # two buses, one line: losing it splits the grid
    lodf, valid, _ = lodf_matrix(np.array([[1.0, 0.0]]), np.array([[1.0, -1.0]]))
    assert not valid[0]


def _run(security):
    flow0 = (PTDF @ np.array([90.0, 0.0, -90.0]))[None, :]
    np.testing.assert_allclose(flow0[0], [30.0, 60.0, 30.0])
    headroom = np.array([[0.0, 50.0, 0.0]])
    disp = np.array([[90.0, 0.0, 0.0]])
    res = np.zeros((1, 3))
    return redispatch(flow0, PTDF, S_NOM, headroom, disp, res, limit_pu=1.0,
                      costs=_costs(), security=security)


def test_no_redispatch_without_n_minus_1():
    rd = _run(None)
    assert rd.up.sum() == 0 and rd.down_disp.sum() == 0


def test_n_minus_1_hand_computed_answer():
    lodf, valid, _ = lodf_matrix(PTDF, INC)
    sec = Security(lodf=lodf, outages=valid, monitored=np.ones(3, bool), limit_pu=0.8)
    rd = _run(sec)
    np.testing.assert_allclose(rd.up[0], [0.0, 10.0, 0.0], atol=1e-6)
    np.testing.assert_allclose(rd.down_disp[0], [10.0, 0.0, 0.0], atol=1e-6)
    assert rd.unresolved[0] < 1e-6
    # every post-fault flow within 80% after the redispatch
    f = rd.flow[0]
    for k in range(3):
        post = f + lodf[:, k] * f[k]
        post[k] = 0.0
        assert (np.abs(post) <= 0.8 * S_NOM + 1e-6).all()


def test_one_circuit_of_a_double_line_by_hand():
    """Line 13 has two circuits (each reactance 2, together 1). Losing one: the remaining network
    is circuit 13 (x = 2) parallel to path 1-2-3 (x = 2), so the 60 MW of line 13 split 45/45:
    f12' = 30 + 15 = 45, f13' (one circuit left) = 45, f23' = 45.
    By the formula: M[:, 13] = (1/3, 2/3, 1/3), phi = 1/2, d = 1 - 1/3 = 2/3:
    LODF[12, 13] = 0.5 * (1/3) / (2/3) = 1/4, LODF[13, 13] = 0.5 / (2/3) - 1 = -1/4."""
    lodf, valid, phi = lodf_matrix(PTDF, INC, circuits=np.array([1, 2, 1]))
    np.testing.assert_allclose(lodf[:, 1], [0.25, -0.25, 0.25])
    f = np.array([30.0, 60.0, 30.0])
    np.testing.assert_allclose(f + lodf[:, 1] * f[1], [45.0, 45.0, 45.0])
    assert valid[1] and phi[1] == 0.5
    # the single-circuit line 12 still trips completely
    np.testing.assert_allclose(lodf[0, 0], -1.0)


def test_double_circuit_bridge_is_a_valid_outage():
    lodf, valid, phi = lodf_matrix(np.array([[1.0, 0.0]]), np.array([[1.0, -1.0]]),
                                   circuits=np.array([2]))
    assert valid[0]
    np.testing.assert_allclose(lodf[0, 0], 0.0)   # the remaining circuit carries all the flow
