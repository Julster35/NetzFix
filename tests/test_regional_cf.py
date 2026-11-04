"""A27: plain profile assets use per-bus capacity factors when given (hand-computed)."""

import numpy as np
import pandas as pd

from netzfix.sim.behaviours import Context
from netzfix.sim.engine import simulate


def test_regional_cf_replaces_national_profile_per_bus():
    idx = pd.date_range("2024-06-01", periods=2, freq="h", tz="UTC")
    ts = pd.DataFrame({"wind_onshore": [100.0, 50.0]}, index=idx)     # national: cf 0.5, 0.25
    reg = pd.DataFrame({"a": [0.9, 0.1], "b": [0.1, 0.4]}, index=idx)  # bus a / bus b
    assets = [{"id": f"w{b}", "kind": "producer", "carrier": "wind_onshore", "bus": b,
               "p_nom": 100.0, "p_nom_monthly": [100.0] * 12,
               "behaviour": {"type": "national_profile", "carrier": "wind_onshore"}}
              for b in ("a", "b")]
    borders = pd.DataFrame({"bus": ["a"], "capacity_mw": [1.0], "border_id": ["x"]})
    common = dict(assets=assets, buses=["a", "b"], ptdf=np.zeros((0, 2)), branches=[],
                  s_nom=np.zeros(0), borders=borders, balancing="border")
    nat = simulate(ctx=Context(ts=ts, capacity={"wind_onshore": 200.0}), **common)
    regional = simulate(ctx=Context(ts=ts, capacity={"wind_onshore": 200.0},
                                    regional_cf={"wind_onshore": reg}), **common)
    assert np.allclose(nat.res_bus, [[50.0, 50.0], [25.0, 25.0]])
    assert np.allclose(regional.res_bus, [[90.0, 10.0], [10.0, 40.0]])
