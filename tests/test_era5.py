from netzfix.config import load_config
from netzfix.data.era5 import snap_bounds


def test_snap_bounds_pads_and_snaps_outward():
    # hand-computed: 5.87 - 0.25 = 5.62 -> 5.5; 47.27 - 0.25 = 47.02 -> 47.0;
    # 15.04 + 0.25 = 15.29 -> 15.5; 55.29 + 0.25 = 55.54 -> 55.75
    assert snap_bounds((5.87, 47.27, 15.04, 55.29), 0.25) == (5.5, 47.0, 15.5, 55.75)


def test_snap_bounds_on_grid_points_only_adds_margin():
    assert snap_bounds((6.0, 48.0, 15.0, 55.0), 0.25) == (5.75, 47.75, 15.25, 55.25)


def test_weather_config_defaults():
    w = load_config()["weather"]
    assert w["module"] == "era5"
    assert w["margin_deg"] == 0.25
    assert set(w["features"]) == {"wind", "influx", "temperature"}
