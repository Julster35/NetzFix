"""Engine tests on a 3-bus triangle with equal reactances (hand-computable flows).

The time series here are test fixtures, not data.
"""

import numpy as np
import pandas as pd
import pypsa
import pytest

from netzfix.network.grid import ptdf
from netzfix.sim.behaviours import Context, evaluate
from netzfix.sim.engine import simulate


@pytest.fixture
def tri():
    n = pypsa.Network()
    n.add("Bus", ["A", "B", "C"], v_nom=380)
    n.add("Line", ["AB", "BC", "CA"], bus0=["A", "B", "C"], bus1=["B", "C", "A"],
          x=10.0, r=0.0, s_nom=100.0)
    P, branches, buses = ptdf(n)
    s_nom = np.full(len(branches), 100.0)
    borders = pd.DataFrame({"border_id": ["X"], "bus": ["C"], "capacity_mw": [1000.0]})
    return P, branches, buses, s_nom, borders


def ctx_fixture(T=48, **cols):
    idx = pd.date_range("2024-01-01", periods=T, freq="h", tz="UTC")
    base = {"load": 90.0, "pumped_hydro_load": 0.0, "gas": 0.0, "wind_onshore": 50.0,
            "pumped_hydro": 0.0, "price_de_lu": 50.0}
    base.update(cols)
    ts = pd.DataFrame({k: (v if np.ndim(v) else np.full(T, v)) for k, v in base.items()},
                      index=idx)
    return Context(ts=ts, capacity={"gas": 100.0, "wind_onshore": 100.0}, seed=1)


def producer(id_, bus, carrier, p_nom, **beh):
    return {"id": id_, "kind": "producer", "bus": bus, "carrier": carrier, "p_nom": p_nom,
            "behaviour": {"type": "national_profile", **beh}}


def consumer(id_, bus, share):
    return {"id": id_, "kind": "consumer", "bus": bus, "carrier": "load",
            "behaviour": {"type": "demand_share", "share": share}}


def test_triangle_flows_split_two_to_one(tri):
    P, branches, buses, s_nom, borders = tri
    inj = np.zeros(3)
    inj[buses.index("A")], inj[buses.index("B")] = 90, -90
    f = dict(zip(branches, P @ inj, strict=True))
    assert f["Line:AB"] == pytest.approx(60)
    assert f["Line:BC"] == pytest.approx(-30)   # flow C->B is +30, i.e. B->C is -30
    assert f["Line:CA"] == pytest.approx(-30)   # A->C is +30


def test_injections_balance_and_border_takes_rest(tri):
    P, branches, buses, s_nom, borders = tri
    ctx = ctx_fixture()
    assets = [producer("w", "A", "wind_onshore", 100), consumer("d", "B", 1.0)]
    r = simulate(assets, buses, P, branches, s_nom, borders, ctx, balancing="border")
    assert np.allclose(r.injection.sum(axis=1), 0)
    assert np.allclose(r.border["X"], 90 - 50)       # import 40 MW at C


def test_keep_trade_displaces_dispatchable(tri):
    P, branches, buses, s_nom, borders = tri
    # history: load 90, wind 50, gas 40 -> net import 0
    ctx = ctx_fixture(gas=40.0)
    base = [producer("w", "A", "wind_onshore", 100), producer("g", "C", "gas", 100),
            consumer("d", "B", 1.0)]
    r0 = simulate(base, buses, P, branches, s_nom, borders, ctx)
    assert np.allclose(r0.border["X"], 0) and np.allclose(r0.by_carrier["gas"], 40)
    # add 30 MW constant producer: gas must fall to 10, trade unchanged
    extra = {"id": "new", "kind": "producer", "bus": "A", "carrier": "solar", "p_nom": 30,
             "behaviour": {"type": "constant", "p_mw": 30}}
    r1 = simulate(base + [extra], buses, P, branches, s_nom, borders, ctx)
    assert np.allclose(r1.by_carrier["gas"], 10)
    assert np.allclose(r1.border["X"], 0) and np.allclose(r1.trade_deviation, 0)


def test_redispatch_removes_overload_with_minimum_volume(tri):
    from netzfix.sim.redispatch import redispatch

    P, branches, buses, s_nom, borders = tri
    ia, ib, ic = (buses.index(x) for x in "ABC")
    # 150 MW from A to B: AB carries 100 (limit 100 -> ok), now push 180: AB = 120 > 100
    inj = np.zeros((1, 3))
    inj[0, ia], inj[0, ib] = 180, -180
    f0 = inj @ P.T
    head = np.zeros((1, 3))
    head[0, ib] = 500                       # a plant at B can ramp up
    disp = np.zeros((1, 3))
    disp[0, ia] = 180                       # the plant at A can ramp down
    rd = redispatch(f0, P, s_nom, head, disp, np.zeros((1, 3)), limit_pu=1.0)
    assert np.abs(rd.flow).max() <= 100 + 1e-6
    # AB flow = 2/3 of the A->B transfer; must fall from 120 to 100 -> transfer 150 -> shift 30 MW
    assert rd.up.sum() == pytest.approx(30, abs=1e-4)
    assert rd.down_disp.sum() == pytest.approx(30, abs=1e-4)
    assert rd.unresolved.sum() == pytest.approx(0)


def test_outage_rate_and_seed_reproducibility():
    ctx = ctx_fixture(T=200_000)
    a = producer("w", "A", "wind_onshore", 100.0,
                 modifiers=[{"type": "outage", "forced_outage_rate": 0.1, "mttr_hours": 24}])
    x = evaluate(a, ctx)
    assert (x == 0).mean() == pytest.approx(0.1, abs=0.02)
    ctx2 = ctx_fixture(T=200_000)
    assert np.array_equal(x, evaluate(a, ctx2))


def test_noise_has_requested_std():
    ctx = ctx_fixture(T=200_000)
    a = producer("w", "A", "wind_onshore", 100.0,
                 modifiers=[{"type": "noise", "sigma": 0.1, "phi": 0.5}])
    x = evaluate(a, ctx) / 50.0 - 1.0          # base output is 50 MW
    assert x.std() == pytest.approx(0.1, rel=0.05)


def test_daily_arbitrage_energy_balance():
    T = 48
    price = np.tile(np.r_[np.full(12, 10.0), np.full(12, 100.0)], 2)
    ctx = ctx_fixture(T=T, price_de_lu=price)
    a = {"id": "bat", "kind": "storage", "bus": "A", "carrier": "battery", "p_nom": 10.0,
         "behaviour": {"type": "daily_arbitrage", "energy_hours": 4, "efficiency": 0.9}}
    x = evaluate(a, ctx)
    assert -x[x < 0].sum() == pytest.approx(80.0)          # 2 days x 4 h x 10 MW charged
    assert x[x > 0].sum() == pytest.approx(72.0)           # 90% discharged
