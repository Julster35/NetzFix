"""FastAPI app for the local playground. Run: `uv run netzfix serve` (http://127.0.0.1:8765)."""

from __future__ import annotations

from functools import lru_cache

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from netzfix.config import REPO_ROOT
from netzfix.server.state import SCENARIOS, Playground

app = FastAPI(title="NetzFix playground")
DIST = REPO_ROOT / "web" / "dist"


@lru_cache(maxsize=1)
def pg() -> Playground:
    return Playground()


class SimRequest(BaseModel):
    start: str = "2024-01-15T00:00"
    hours: int = 168
    balancing: str | None = None
    seed: int | None = None
    redispatch_limit: float | None = None   # e.g. 1.0 or 0.7; None = off


@app.get("/api/grid")
def get_grid() -> dict:
    return pg().grid_payload()


@app.get("/api/assets")
def get_assets() -> list[dict]:
    return pg().assets_payload()


@app.post("/api/assets")
def add_asset(a: dict) -> dict:
    try:
        return pg().add_asset(a)
    except (KeyError, ValueError) as e:
        raise HTTPException(400, str(e)) from e


@app.put("/api/assets/{asset_id:path}")
def update_asset(asset_id: str, a: dict) -> dict:
    try:
        return pg().update_asset(asset_id, a)
    except KeyError as e:
        raise HTTPException(404, str(e)) from e
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@app.delete("/api/assets/{asset_id:path}")
def delete_asset(asset_id: str) -> dict:
    try:
        pg().remove_asset(asset_id)
    except KeyError as e:
        raise HTTPException(404, str(e)) from e
    return {"ok": True}


@app.post("/api/simulate")
def run(req: SimRequest) -> dict:
    try:
        return pg().run(req.start, req.hours, req.balancing, req.seed,
                        req.redispatch_limit)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@app.get("/api/scenario")
def scenario() -> dict:
    return pg().scenario.to_json()


@app.put("/api/scenario/settings")
def settings(s: dict) -> dict:
    pg().scenario.settings.update(s)
    return pg().scenario.settings


@app.get("/api/scenarios")
def scenarios() -> list[str]:
    return ["baseline"] + sorted(p.stem for p in SCENARIOS.glob("*.json"))


@app.post("/api/scenarios/{name}/save")
def save(name: str) -> dict:
    return {"path": str(pg().save(name))}


@app.post("/api/scenarios/{name}/load")
def load(name: str) -> dict:
    try:
        pg().load(name)
    except FileNotFoundError as e:
        raise HTTPException(404, name) from e
    return pg().scenario.to_json()


if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="static")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(DIST / "index.html")
