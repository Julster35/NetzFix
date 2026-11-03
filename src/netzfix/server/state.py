"""Playground state: the static 2024 grid + baseline assets + the user's edits.

A scenario is stored as edits on top of the baseline (added / modified / removed assets plus
settings), so it stays small, readable and reproducible: `scenarios/<name>.json`.
"""

from __future__ import annotations

import base64
import copy
import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from shapely import wkt as shp_wkt

from netzfix.config import DATA_PROCESSED, REPO_ROOT
from netzfix.network import grid as gridmod
from netzfix.sim.behaviours import Context, schema
from netzfix.sim.engine import historical_import, simulate

SCENARIOS = REPO_ROOT / "scenarios"
ASSETS_FILE = DATA_PROCESSED / "assets_baseline_2024.parquet"
SMARD_FILE = DATA_PROCESSED / "smard_DE_2024.parquet"
CBPF_FILE = DATA_PROCESSED / "cbpf_DE_2024.parquet"


def _b64(a: np.ndarray, dtype: str) -> str:
    return base64.b64encode(np.ascontiguousarray(a, dtype=dtype).tobytes()).decode("ascii")


@dataclass
class Scenario:
    name: str = "baseline"
    added: dict[str, dict] = field(default_factory=dict)
    modified: dict[str, dict] = field(default_factory=dict)
    removed: set[str] = field(default_factory=set)
    settings: dict = field(default_factory=lambda: {"balancing": "keep_trade", "seed": 0})

    def to_json(self) -> dict:
        return {"name": self.name, "added": self.added, "modified": self.modified,
                "removed": sorted(self.removed), "settings": self.settings}

    @classmethod
    def from_json(cls, d: dict) -> Scenario:
        return cls(d["name"], d.get("added", {}), d.get("modified", {}), set(d.get("removed", [])),
                   d.get("settings", {"balancing": "keep_trade", "seed": 0}))


class Playground:
    def __init__(self) -> None:
        g = gridmod.load()
        self.grid = g
        n = g.network
        self.ptdf, self.branches, self.buses = gridmod.ptdf(n)
        s_line = n.lines.s_nom.to_dict()
        s_tr = n.transformers.s_nom.to_dict()
        self.s_nom = np.array([(s_line if b.startswith("Line:") else s_tr)[b.split(":", 1)[1]]
                               for b in self.branches], dtype=float)
        self.ts = pd.read_parquet(SMARD_FILE)
        if CBPF_FILE.exists():  # measured cross-border physical flows (A18 v1)
            xb = pd.read_parquet(CBPF_FILE).add_prefix("xb_")
            self.ts = self.ts.join(xb, how="left")
            if self.ts[xb.columns].isna().any().any():
                raise ValueError("cross-border flows do not cover all SMARD hours")
            self.ts["domestic_gap"] = historical_import(self.ts) - self.ts[xb.columns].sum(axis=1)
        base = pd.read_parquet(ASSETS_FILE)
        base["behaviour"] = base["behaviour"].map(json.loads)
        base["p_nom_monthly"] = base["p_nom_monthly"].map(
            lambda m: None if m is None else [float(x) for x in m])
        base = base.astype(object).where(base.notna(), None)
        self.baseline: dict[str, dict] = {r["id"]: r for r in base.to_dict("records")}
        # national installed capacity per carrier at each month-end (normalises SMARD profiles)
        self.capacity: dict[str, np.ndarray] = {}
        for a in self.baseline.values():
            if a["kind"] != "consumer" and a["p_nom_monthly"] is not None:
                c = a["carrier"]
                self.capacity[c] = self.capacity.get(c, np.zeros(12)) + np.asarray(
                    a["p_nom_monthly"], float)
        self.scenario = Scenario()
        # shares for the domestic gap: same as demand shares (A21b)
        share = {a["bus"]: a["behaviour"]["share"] for a in self.baseline.values()
                 if a["kind"] == "consumer" and a["behaviour"]["type"] == "demand_share"}
        self.gap_share = np.array([share.get(b, 0.0) for b in self.buses])
        self.gap_share = self.gap_share / self.gap_share.sum()

    # ------------------------------------------------------------------ assets
    def assets(self) -> list[dict]:
        sc = self.scenario
        out = [sc.modified.get(i, a) for i, a in self.baseline.items() if i not in sc.removed]
        return out + list(sc.added.values())

    def add_asset(self, a: dict) -> dict:
        a = copy.deepcopy(a)
        a["id"] = a.get("id") or f"user/{uuid.uuid4().hex[:8]}"
        a["source"] = "user"
        self._validate(a)
        self.scenario.added[a["id"]] = a
        return a

    def update_asset(self, asset_id: str, a: dict) -> dict:
        old = self._get(asset_id)
        a = {**old, **a, "id": asset_id}
        # editing p_nom of a baseline asset scales its monthly fleet profile proportionally
        if "p_nom" in a and old.get("p_nom_monthly") and old.get("p_nom"):
            f = float(a["p_nom"]) / float(old["p_nom"])
            a["p_nom_monthly"] = [x * f for x in old["p_nom_monthly"]]
        self._validate(a)
        if asset_id in self.scenario.added:
            self.scenario.added[asset_id] = a
        else:
            self.scenario.modified[asset_id] = a
        return a

    def remove_asset(self, asset_id: str) -> None:
        self._get(asset_id)
        if self.scenario.added.pop(asset_id, None) is None:
            self.scenario.removed.add(asset_id)
            self.scenario.modified.pop(asset_id, None)

    def _get(self, asset_id: str) -> dict:
        sc = self.scenario
        if asset_id in sc.added:
            return sc.added[asset_id]
        if asset_id in self.baseline and asset_id not in sc.removed:
            return sc.modified.get(asset_id, self.baseline[asset_id])
        raise KeyError(asset_id)

    def _validate(self, a: dict) -> None:
        if a["kind"] not in ("producer", "consumer", "storage"):
            raise ValueError("kind must be producer, consumer or storage")
        if a["bus"] not in set(self.buses):
            raise ValueError(f"unknown bus {a['bus']}")
        if a["bus"].startswith("NB-"):
            raise ValueError("neighbour nodes are boundary equivalents; place assets in Germany")
        if "behaviour" not in a or "type" not in a["behaviour"]:
            raise ValueError("behaviour.type required")

    # ------------------------------------------------------------------ scenarios
    def save(self, name: str) -> Path:
        SCENARIOS.mkdir(exist_ok=True)
        self.scenario.name = name
        p = SCENARIOS / f"{name}.json"
        p.write_text(json.dumps(self.scenario.to_json(), indent=1), encoding="utf-8")
        return p

    def load(self, name: str) -> None:
        if name == "baseline":
            self.scenario = Scenario()
            return
        p = SCENARIOS / f"{name}.json"
        self.scenario = Scenario.from_json(json.loads(p.read_text(encoding="utf-8")))

    # ------------------------------------------------------------------ static payloads
    def grid_payload(self) -> dict:
        n = self.grid.network
        geom = self.grid.line_geometry
        branches = []
        for k, b in enumerate(self.branches):
            comp, bid = b.split(":", 1)
            try:
                coords = [list(c) for c in shp_wkt.loads(geom[bid]).coords]
            except Exception:  # transformers without geometry: straight segment
                df = n.lines if comp == "Line" else n.transformers
                b0, b1 = df.at[bid, "bus0"], df.at[bid, "bus1"]
                coords = [[n.buses.at[b0, "x"], n.buses.at[b0, "y"]],
                          [n.buses.at[b1, "x"], n.buses.at[b1, "y"]]]
            df = n.lines if comp == "Line" else n.transformers
            v = (n.buses.at[df.at[bid, "bus0"], "v_nom"])
            branches.append({"i": k, "id": bid, "kind": comp, "v": float(v),
                             "equivalent": bid.startswith("EQ-"),
                             "s_nom": round(float(self.s_nom[k]), 1),
                             "path": [[round(x, 5), round(y, 5)] for x, y in coords]})
        buses = [{"i": i, "id": b, "lon": round(float(n.buses.at[b, "x"]), 5),
                  "lat": round(float(n.buses.at[b, "y"]), 5), "v": float(n.buses.at[b, "v_nom"]),
                  "virtual": b.startswith("NB-")}
                 for i, b in enumerate(self.buses)]
        borders = self.grid.borders.to_dict("records")
        return {"buses": buses, "branches": branches, "borders": borders,
                "time_range": [str(self.ts.index[0]), str(self.ts.index[-1])],
                "behaviours": schema(),
                "source": {"grid": "PyPSA-Eur OSM network v0.7 (Zenodo 18619025, ODbL 1.0)",
                           "units": "Marktstammdatenregister (DL-DE-BY-2.0)",
                           "timeseries": "SMARD 2024 (Bundesnetzagentur)"}}

    def assets_payload(self) -> list[dict]:
        keep = ("id", "name", "kind", "carrier", "bus", "p_nom", "lon", "lat", "group",
                "n_units", "behaviour", "source")
        return [{k: a.get(k) for k in keep} for a in self.assets()]

    # ------------------------------------------------------------------ simulation
    def simulate(self, ctx: Context, balancing: str = "keep_trade"):
        return simulate(self.assets(), self.buses, self.ptdf, self.branches, self.s_nom,
                        self.grid.borders, ctx, balancing=balancing, gap_share=self.gap_share)

    def run(self, start: str, hours: int, balancing: str | None = None,
            seed: int | None = None, redispatch_limit: float | None = None) -> dict:
        t0 = pd.Timestamp(start)
        t0 = t0.tz_localize("Europe/Berlin") if t0.tzinfo is None else t0
        win = self.ts[(self.ts.index >= t0.tz_convert("UTC"))].iloc[:hours]
        if win.empty:
            raise ValueError("window outside the data range")
        st = self.scenario.settings
        bal = balancing or st.get("balancing", "keep_trade")
        sd = int(seed if seed is not None else st.get("seed", 0))
        ctx = Context(ts=win, capacity=self.capacity, seed=sd)
        r = self.simulate(ctx, balancing=bal)
        T = len(win)
        flow_before = r.flow
        rd_payload: dict = {"enabled": False}
        if redispatch_limit:
            from netzfix.sim.redispatch import redispatch

            rd = redispatch(r.flow, self.ptdf, self.s_nom, r.headroom_bus, r.disp_bus, r.res_bus,
                            limit_pu=float(redispatch_limit))
            v = rd.volume_twh()
            net = rd.up - rd.down_disp - rd.down_res        # T x buses, + = more injection
            r.flow = rd.flow
            r.injection = r.injection + net
            rd_payload = {
                "enabled": True, "limit_pu": float(redispatch_limit),
                "up_i16": _b64(np.clip(np.rint(rd.up), 0, 32767), "<i2"),
                "down_i16": _b64(np.clip(np.rint(rd.down_disp + rd.down_res), 0, 32767), "<i2"),
                "volume_gwh": {k: round(x * 1e3, 1) for k, x in v.items()},
                "unresolved_mwh": round(float(rd.unresolved.sum()), 1),
                "hourly_mw": np.round(rd.up.sum(axis=1), 1).tolist(),
                "flow_before_i16": _b64(np.clip(np.rint(flow_before), -32767, 32767), "<i2"),
            }
        flow = np.clip(np.rint(r.flow), -32767, 32767)
        inj = np.clip(np.rint(r.injection), -32767, 32767)
        loading = np.abs(r.flow) / self.s_nom
        return {
            "redispatch": rd_payload,
            "snapshots": [t.isoformat() for t in win.index],
            "T": T, "n_branches": len(self.branches), "n_buses": len(self.buses),
            "flow_i16": _b64(flow, "<i2"),
            "injection_i16": _b64(inj, "<i2"),
            "by_carrier": {c: np.round(v.to_numpy(), 1).tolist()
                           for c, v in r.by_carrier.items()},
            "border_total": np.round(r.border.sum(axis=1).to_numpy(), 1).tolist(),
            "border_by_country": ({c: np.round(r.border[c].to_numpy(), 1).tolist()
                                   for c in r.border.columns}
                                  if all(len(str(c)) == 2 for c in r.border.columns) else {}),
            "trade_deviation": np.round(r.trade_deviation, 1).tolist(),
            "price": np.round(win["price_de_lu"].to_numpy(), 2).tolist(),
            "kpi": {
                "max_loading": float(loading.max()),
                "line_hours_over_70pct": int((loading > 0.7).sum()),
                "line_hours_over_100pct": int((loading > 1.0).sum()),
                "max_trade_deviation_mw": float(np.abs(r.trade_deviation).max()),
            },
            "settings": {"balancing": bal, "seed": sd, "start": str(win.index[0]), "hours": T},
        }
