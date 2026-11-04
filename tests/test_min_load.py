"""A31: downward redispatch room stops at minimum load (hand-computed)."""

import numpy as np
import pandas as pd

from netzfix.sim.behaviours import Context
from netzfix.sim.engine import simulate


def _unit(uid, bus, p_mw, min_load):
    return {"id": uid, "kind": "producer", "carrier": "lignite", "bus": bus, "p_nom": 100.0,
            "min_load": min_load, "behaviour": {"type": "constant", "p_mw": p_mw}}


def test_down_room_is_output_above_min_load_of_running_units():
    idx = pd.date_range("2024-06-01", periods=1, freq="h", tz="UTC")
    # a: 80 MW, min 55 MW -> room 25; b: 40 MW below min 55 -> room 0; c: no min load -> 30
    assets = [_unit("a", "x", 80.0, 0.55), _unit("b", "x", 40.0, 0.55),
              _unit("c", "y", 30.0, 0.0)]
    r = simulate(assets=assets, buses=["x", "y"], ptdf=np.zeros((0, 2)), branches=[],
                 s_nom=np.zeros(0), borders=pd.DataFrame({"bus": ["x"], "capacity_mw": [1.0],
                                                          "border_id": ["b"]}),
                 ctx=Context(ts=pd.DataFrame(index=idx), capacity={}), balancing="border")
    assert np.allclose(r.disp_bus, [[120.0, 30.0]])
    assert np.allclose(r.down_bus, [[25.0, 30.0]])
    assert np.allclose(r.headroom_bus, [[80.0, 70.0]])
