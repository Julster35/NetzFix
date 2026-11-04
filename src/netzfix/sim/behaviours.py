"""Asset behaviours: how an asset's power evolves over time.

A behaviour is a JSON-serialisable dict:
    {"type": <base type>, ...params, "modifiers": [{"type": "noise", ...}, ...]}
Sign convention of the returned series (MW): producers >= 0 output, consumers >= 0 demand,
storage > 0 discharging / < 0 charging.

Base types use only real 2024 data (SMARD, MaStR) or user-set constants. Stochastic modifiers
take user-chosen parameters; they are scenario inputs, not data, and the UI labels them so.
"""

from __future__ import annotations

import zlib
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

# SMARD carriers whose national output defines the "national_profile" capacity factor
PROFILE_CARRIERS = (
    "solar", "wind_onshore", "wind_offshore", "biomass", "hydro", "lignite", "hard_coal",
    "gas", "other_conventional", "other_renewable",
)
DISPATCHABLE = ("lignite", "hard_coal", "gas", "other_conventional")


@dataclass
class Context:
    """Everything a behaviour may read. `ts` holds SMARD columns for the simulated window."""

    ts: pd.DataFrame                         # index: UTC snapshots; SMARD columns (MW)
    # baseline MaStR capacity per carrier (MW): a scalar, or 12 month-end values for the year
    capacity: dict[str, float | np.ndarray]
    seed: int = 0
    rng_streams: dict[str, np.random.Generator] = field(default_factory=dict)
    # A27: per-bus capacity factors (index UTC hours, columns buses) replacing the national
    # profile of plain profile assets of these carriers (engine, vectorised path)
    regional_cf: dict[str, pd.DataFrame] | None = None

    @property
    def n(self) -> int:
        return len(self.ts)

    @property
    def month_idx(self) -> np.ndarray:
        """0-11, month of each snapshot in German local time."""
        if not hasattr(self, "_month_idx"):
            self._month_idx = self.ts.index.tz_convert("Europe/Berlin").month.to_numpy() - 1
        return self._month_idx

    def by_month(self, value: float | np.ndarray | list) -> np.ndarray:
        """Expand a scalar or a 12-vector of month-end values to the snapshots."""
        v = np.asarray(value, dtype="float64")
        return np.full(self.n, float(v)) if v.ndim == 0 else v[self.month_idx]

    def capacity_factor(self, carrier: str) -> np.ndarray:
        """National output / installed capacity. If units of this carrier replay their own
        2024 output (A26), the column `residual:<carrier>` (SMARD minus replayed units) is used,
        and `capacity` already holds the residual capacity."""
        if carrier not in self.ts or carrier not in self.capacity:
            raise KeyError(f"no national profile for carrier {carrier!r}")
        col = f"residual:{carrier}" if f"residual:{carrier}" in self.ts else carrier
        cap = self.by_month(self.capacity[carrier])
        with np.errstate(divide="ignore", invalid="ignore"):
            cf = np.where(cap > 0, self.ts[col].to_numpy(dtype="float64") / cap, 0.0)
        return np.clip(cf, 0.0, 1.0)

    def rng(self, key: str) -> np.random.Generator:
        """Independent, reproducible stream per asset+modifier."""
        if key not in self.rng_streams:
            # crc32, not hash(): str hashes are salted per process and would break reproducibility
            ss = np.random.SeedSequence([self.seed, zlib.crc32(key.encode("utf-8"))])
            self.rng_streams[key] = np.random.default_rng(ss)
        return self.rng_streams[key]


# ---------------------------------------------------------------- base behaviours

def asset_capacity(a: dict, ctx: Context) -> np.ndarray:
    """Installed MW per snapshot: monthly fleet values for baseline assets, else p_nom."""
    m = a.get("p_nom_monthly")
    return ctx.by_month(m if m is not None and len(m) == 12 else (a.get("p_nom") or 0.0))


def _national_profile(a: dict, b: dict, ctx: Context) -> np.ndarray:
    return asset_capacity(a, ctx) * ctx.capacity_factor(b.get("carrier", a["carrier"]))


def _demand_share(a: dict, b: dict, ctx: Context) -> np.ndarray:
    return b["share"] * ctx.ts["load"].to_numpy(dtype="float64")


def _constant(a: dict, b: dict, ctx: Context) -> np.ndarray:
    return np.full(ctx.n, float(b["p_mw"]))


def _replay_entsoe(a: dict, b: dict, ctx: Context) -> np.ndarray:
    """Share of a plant's actual 2024 output (ENTSO-E TR 16.1.A, A26)."""
    return float(b["share"]) * ctx.ts[f"entsoe:{b['group']}"].to_numpy(dtype="float64")


def _replay_pumped_hydro(a: dict, b: dict, ctx: Context) -> np.ndarray:
    share = asset_capacity(a, ctx) / ctx.by_month(ctx.capacity["pumped_hydro"])
    return share * (ctx.ts["pumped_hydro"].to_numpy() - ctx.ts["pumped_hydro_load"].to_numpy())


def _daily_arbitrage(a: dict, b: dict, ctx: Context) -> np.ndarray:
    """Rule, not optimisation: per local day, charge in the cheapest k hours and discharge in the
    most expensive k hours of the price signal, k = floor(energy_hours). Round-trip efficiency
    reduces discharge energy. Assumes hourly snapshots."""
    p = a["p_nom"]
    k = int(b.get("energy_hours", 4))
    eta = float(b.get("efficiency", 1.0))
    price = ctx.ts[b.get("signal", "price_de_lu")]
    out = np.zeros(ctx.n)
    local_day = price.index.tz_convert("Europe/Berlin").date
    for _, idx in pd.Series(np.arange(ctx.n), index=local_day).groupby(level=0):
        pos = idx.to_numpy()
        if len(pos) < 2 * k:
            continue
        order = pos[np.argsort(price.to_numpy()[pos], kind="stable")]
        cheap, dear = order[:k], order[-k:]
        if price.to_numpy()[dear].mean() * eta <= price.to_numpy()[cheap].mean():
            continue  # no profitable spread that day
        out[cheap] -= p
        out[dear] += p * eta
    return out


BASE = {
    "national_profile": _national_profile,
    "demand_share": _demand_share,
    "constant": _constant,
    "replay_pumped_hydro": _replay_pumped_hydro,
    "replay_entsoe": _replay_entsoe,
    "daily_arbitrage": _daily_arbitrage,
}


# ---------------------------------------------------------------- stochastic modifiers

def _noise(x: np.ndarray, m: dict, key: str, ctx: Context) -> np.ndarray:
    """Multiplicative AR(1) Gaussian noise: x_t * (1 + e_t),
    e_t = phi e_{t-1} + sigma*sqrt(1-phi^2) z_t.
    Stationary std of e is sigma."""
    sigma, phi = float(m["sigma"]), float(m.get("phi", 0.0))
    z = ctx.rng(key).standard_normal(len(x))
    e = np.empty(len(x))
    e[0] = sigma * z[0]
    scale = sigma * np.sqrt(max(1.0 - phi * phi, 0.0))
    for t in range(1, len(x)):
        e[t] = phi * e[t - 1] + scale * z[t]
    return x * (1.0 + e)


def _outage(x: np.ndarray, m: dict, key: str, ctx: Context) -> np.ndarray:
    """Two-state Markov availability. forced_outage_rate = long-run share of hours unavailable,
    mttr_hours = mean outage duration.
    Repair prob mu = 1/mttr; failure prob lam = mu*FOR/(1-FOR)."""
    q, mttr = float(m["forced_outage_rate"]), float(m["mttr_hours"])
    if not 0 <= q < 1 or mttr < 1:
        raise ValueError("need 0 <= forced_outage_rate < 1 and mttr_hours >= 1")
    mu = 1.0 / mttr
    lam = mu * q / (1.0 - q)
    u = ctx.rng(key).random(len(x))
    up = np.empty(len(x), dtype=bool)
    up[0] = u[0] >= q
    for t in range(1, len(x)):
        up[t] = (u[t] >= lam) if up[t - 1] else (u[t] < mu)
    return x * up


MODIFIERS = {"noise": _noise, "outage": _outage}


def evaluate(asset: dict[str, Any], ctx: Context) -> np.ndarray:
    b = asset["behaviour"]
    x = BASE[b["type"]](asset, b, ctx)
    for i, m in enumerate(b.get("modifiers", [])):
        x = MODIFIERS[m["type"]](x, m, f"{asset['id']}/{i}/{m['type']}", ctx)
    if asset["kind"] in ("producer", "consumer"):
        x = np.clip(x, 0.0, None)
        if asset["kind"] == "producer" and asset.get("p_nom"):
            x = np.minimum(x, asset_capacity(asset, ctx))
    return x


def is_plain_profile(asset: dict) -> bool:
    """True if the asset is a pure national_profile without modifiers (vectorisable)."""
    b = asset["behaviour"]
    return b["type"] == "national_profile" and not b.get("modifiers")


def schema() -> dict:
    """Behaviour catalogue for the UI."""
    return {
        "base": {
            "national_profile": {"params": {"carrier": list(PROFILE_CARRIERS)},
                                 "note": "rated MW x 2024 national capacity factor "
                                         "(SMARD / MaStR)"},
            "demand_share": {"params": {"share": "fraction of national load"}},
            "constant": {"params": {"p_mw": "MW"}},
            "replay_pumped_hydro": {"params": {}, "note": "pro-rata share of 2024 pumped storage"},
            "replay_entsoe": {"params": {"group": "ENTSO-E production unit", "share": "0-1"},
                              "note": "actual 2024 output of the plant (ENTSO-E 16.1.A)"},
            "daily_arbitrage": {"params": {"energy_hours": "h", "efficiency": "0-1",
                                           "signal": "price_de_lu"},
                                "note": "rule: charge cheapest / discharge dearest hours per day"},
        },
        "modifiers": {
            "noise": {"params": {"sigma": "std of relative error", "phi": "AR(1) 0-1"}},
            "outage": {"params": {"forced_outage_rate": "0-1", "mttr_hours": ">= 1"}},
        },
        "note": "Modifier parameters are user scenario inputs, not data.",
    }
