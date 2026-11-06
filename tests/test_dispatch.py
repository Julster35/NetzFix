"""Market v1 (A39): merit order on a toy fleet with hand-computed answers.

Three units, marginal cost 10 / 30 / 20 EUR/MWh, 50 MW each.
- need 70 MW: cheapest first -> unit 0 (10) 50 MW, unit 2 (20) 20 MW, unit 1 (30) 0;
  price = 20 (unit 2 is marginal).
- need 0: nothing runs, no price.
- need 180: all 150 MW run, shortfall 30, price undefined (NaN), never invented.
- hour 2 with unit 0 at 0 MW capacity and need 70: unit 2 50 MW, unit 1 20 MW, price 30.
"""

import numpy as np

from netzfix.markets.dispatch import merit_order


def test_merit_order_by_hand():
    mc = np.tile([10.0, 30.0, 20.0], (4, 1))
    cap = np.array([[50.0, 50, 50], [50, 50, 50], [50, 50, 50], [0, 50, 50]])
    need = np.array([70.0, 0.0, 180.0, 70.0])
    r = merit_order(need, cap, mc)
    np.testing.assert_allclose(r.gen[0], [50, 0, 20])
    assert r.price[0] == 20.0 and r.marginal[0] == 2
    assert r.gen[1].sum() == 0 and np.isnan(r.price[1])
    np.testing.assert_allclose(r.gen[2], [50, 50, 50])
    assert r.shortfall[2] == 30.0 and np.isnan(r.price[2])
    np.testing.assert_allclose(r.gen[3], [0, 20, 50])
    assert r.price[3] == 30.0


def test_dispatch_meets_need_exactly():
    rng = np.random.default_rng(0)
    mc, cap = rng.uniform(5, 100, (24, 30)), rng.uniform(0, 100, (24, 30))
    need = cap.sum(axis=1) * 0.6
    r = merit_order(need, cap, mc)
    np.testing.assert_allclose(r.gen.sum(axis=1), need)
    assert (r.gen <= cap + 1e-9).all() and (r.gen >= 0).all()
    # every unit cheaper than the marginal one runs at capacity, every dearer one is off
    for t in range(24):
        m = r.marginal[t]
        cheaper, dearer = mc[t] < mc[t, m], mc[t] > mc[t, m]
        np.testing.assert_allclose(r.gen[t, cheaper], cap[t, cheaper])
        assert (r.gen[t, dearer] == 0).all()
