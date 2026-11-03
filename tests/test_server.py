"""API smoke test on the real processed data (skipped if the data have not been built)."""

import pytest

from netzfix.server.state import ASSETS_FILE, SMARD_FILE

pytestmark = pytest.mark.skipif(not (ASSETS_FILE.exists() and SMARD_FILE.exists()),
                                reason="run `uv run netzfix build` first")


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient

    from netzfix.server.app import app, pg

    pg.cache_clear()
    return TestClient(app)


def test_grid_and_assets(client):
    g = client.get("/api/grid").json()
    assert len(g["buses"]) > 700 and len(g["branches"]) > 1000 and len(g["borders"]) > 40
    a = client.get("/api/assets").json()
    assert {x["kind"] for x in a} == {"producer", "consumer", "storage"}


def test_add_asset_changes_flows_and_keeps_trade(client):
    base = client.post("/api/simulate", json={"start": "2024-06-03T00:00", "hours": 48}).json()
    bus = client.get("/api/grid").json()["buses"][0]["id"]
    new = client.post("/api/assets", json={
        "kind": "producer", "carrier": "solar", "bus": bus, "p_nom": 500,
        "behaviour": {"type": "national_profile", "carrier": "solar"}}).json()
    run = client.post("/api/simulate", json={"start": "2024-06-03T00:00", "hours": 48}).json()
    assert run["flow_i16"] != base["flow_i16"]
    assert run["kpi"]["max_trade_deviation_mw"] < 1.0   # dispatchables absorbed the new solar
    assert client.delete(f"/api/assets/{new['id']}").json()["ok"]


def test_scenario_roundtrip(client, tmp_path, monkeypatch):
    import netzfix.server.state as st

    monkeypatch.setattr(st, "SCENARIOS", tmp_path)
    bus = client.get("/api/grid").json()["buses"][1]["id"]
    client.post("/api/assets", json={"kind": "consumer", "carrier": "load", "bus": bus,
                                     "p_nom": 100, "behaviour": {"type": "constant", "p_mw": 100}})
    client.post("/api/scenarios/test1/save")
    client.post("/api/scenarios/baseline/load")
    assert client.get("/api/scenario").json()["added"] == {}
    client.post("/api/scenarios/test1/load")
    assert len(client.get("/api/scenario").json()["added"]) == 1
