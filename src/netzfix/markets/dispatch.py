"""Market stage of design A, version 1: uniform-price merit-order dispatch of thermal units (A39).

Per hour t the thermal fleet must produce `need[t]` MW: what lignite, hard coal and gas plants
produced in reality (SMARD), because load, renewables, other generation and cross-border trade are
held at their 2024 values (keep_trade, A18). The cheapest available capacity is dispatched first
(marginal cost A30 with the price set A29); the uniform price is the marginal cost of the last
unit needed (the shadow price of the balance of this LP). Hours where the fleet cannot cover the
need are reported as shortfall (price = NaN), never filled with an invented value.

Fleet: individual units (>= 10 MW, technology from MaStR, `unit_technology_2024.csv`) and the
aggregated small-unit groups (gas -> gas_gt, hard coal -> hard_coal_sub, lignite -> lignite,
assumption A39); capacity per month from `p_nom_monthly`; grid-reserve units (A32) are not in
the market. Not in version 1: CHP must-run, start-up costs, minimum load, storage, imports
responding to price (all fixed at 2024 values or absent).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from netzfix.config import DATA_PROCESSED, load_config
from netzfix.markets.prices import marginal_cost, price_table

THERMAL = ("lignite", "hard_coal", "gas")
AGG_TECH = {"gas": "gas_gt", "hard_coal": "hard_coal_sub", "lignite": "lignite"}   # A39


@dataclass
class MarketResult:
    gen: np.ndarray          # T x units, MW
    price: np.ndarray        # T, EUR/MWh (NaN in shortfall hours)
    shortfall: np.ndarray    # T, MW the fleet could not cover
    marginal: np.ndarray     # T, index of the price-setting unit (-1 if none)


def merit_order(need: np.ndarray, cap: np.ndarray, mc: np.ndarray) -> MarketResult:
    """Cheapest-first dispatch per hour. need: T; cap, mc: T x N. Equivalent to the LP
    min sum(mc * g) s.t. sum(g) = need, 0 <= g <= cap; price = mc of the marginal unit."""
    T, N = cap.shape
    gen = np.zeros((T, N))
    price = np.full(T, np.nan)
    short = np.zeros(T)
    marg = np.full(T, -1)
    for t in range(T):
        q = max(float(need[t]), 0.0)
        if q <= 0:
            continue
        order = np.argsort(mc[t], kind="stable")
        c = cap[t, order]
        cum = np.cumsum(c)
        k = int(np.searchsorted(cum, q - 1e-9))
        if k >= N:
            gen[t, order] = c
            short[t] = q - cum[-1]
            continue
        g = c.copy()
        g[k] = q - (cum[k - 1] if k > 0 else 0.0)
        g[k + 1:] = 0.0
        gen[t, order] = g
        price[t] = mc[t, order[k]]
        marg[t] = order[k]
    return MarketResult(gen, price, short, marg)


def fleet(assets: list[dict], index: pd.DatetimeIndex, cfg: dict | None = None) -> pd.DataFrame:
    """Thermal market fleet: id, carrier, technology, monthly capacity (array of 12)."""
    cfg = cfg or load_config()
    tech = pd.read_csv(DATA_PROCESSED / "unit_technology_2024.csv").set_index("id")["technology"]
    rows = []
    for a in assets:
        if a.get("kind") != "producer" or a.get("carrier") not in THERMAL or a.get("reserve"):
            continue
        t = tech.get(a["id"]) if a.get("group") == "unit" else AGG_TECH[a["carrier"]]
        if t is None or t not in cfg["plant_costs"]["technologies"]:
            t = AGG_TECH[a["carrier"]]
        pm = a.get("p_nom_monthly")
        pm = np.full(12, float(a["p_nom"])) if pm is None else np.asarray(pm, float)
        rows.append({"id": a["id"], "carrier": a["carrier"], "technology": t, "p_nom_m": pm})
    return pd.DataFrame(rows)


def run(assets: list[dict], ts: pd.DataFrame, cfg: dict | None = None) -> tuple[MarketResult,
                                                                                  pd.DataFrame]:
    """Version-1 market for the hours of `ts` (SMARD columns, UTC index)."""
    cfg = cfg or load_config()
    fl = fleet(assets, ts.index, cfg)
    prices = price_table(ts.index, cfg=cfg, required=("co2", "gas", "hard_coal", "lignite"))
    techs = cfg["plant_costs"]["technologies"]
    mc_t = {t: marginal_cost(techs[t], prices) for t in fl.technology.unique()}
    mc = np.stack([mc_t[t] for t in fl.technology], axis=1)
    month = ts.index.tz_convert("Europe/Berlin").month.to_numpy() - 1
    cap = np.stack([p[month] for p in fl.p_nom_m], axis=1)
    need = ts[list(THERMAL)].sum(axis=1).to_numpy(dtype=float)
    return merit_order(need, cap, mc), fl
