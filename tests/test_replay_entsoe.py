"""A26: replayed units and the residual national profile (hand-computed)."""

import numpy as np
import pandas as pd

from netzfix.sim.behaviours import Context, evaluate


def _ctx() -> Context:
    idx = pd.date_range("2024-01-01", periods=2, freq="h", tz="UTC")
    ts = pd.DataFrame({"lignite": [1000.0, 800.0],          # SMARD national output
                       "residual:lignite": [400.0, 0.0],     # minus replayed plants
                       "entsoe:P1": [600.0, 900.0]}, index=idx)
    # residual capacity 1,000 MW (replayed plants' capacity already removed)
    return Context(ts=ts, capacity={"lignite": 1000.0})


def test_residual_profile_uses_residual_column():
    # cf = residual / residual capacity = 0.4, 0.0 -> a 500 MW plant gives 200, 0 MW
    a = {"id": "x", "kind": "producer", "carrier": "lignite", "p_nom": 500.0,
         "behaviour": {"type": "national_profile", "carrier": "lignite"}}
    assert np.allclose(evaluate(a, _ctx()), [200.0, 0.0])


def test_replay_shares_plant_output_and_caps_at_p_nom():
    # 40% of P1: 240, 360 MW; capped at p_nom 300 -> 240, 300
    a = {"id": "y", "kind": "producer", "carrier": "lignite", "p_nom": 300.0,
         "behaviour": {"type": "replay_entsoe", "group": "P1", "share": 0.4}}
    assert np.allclose(evaluate(a, _ctx()), [240.0, 300.0])
