"""Simulation engine: assets + behaviours -> bus injections -> DC line flows (no optimisation).

Per snapshot t:
  injection[bus] = sum(producers) - sum(consumers) + storage + border[bus]
Border injections close the balance (sum = 0), so PTDF flows are independent of the slack bus.

Balancing modes:
- "keep_trade" (default): the border carries the historical 2024 net import from SMARD
  (load + pumped-storage load - generation of all carriers). Any extra surplus/deficit created by
  scenario edits is absorbed by dispatchable producers (lignite, hard coal, gas, other conventional)
  pro rata to their output (down) or headroom (up); what they cannot absorb goes to the border and
  is reported as `trade_deviation`.
- "border": the border absorbs every imbalance; dispatchables follow their behaviour.
Border injections are split over border points in proportion to their capacity (A18, v0).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from netzfix.sim.behaviours import DISPATCHABLE, Context, evaluate, is_plain_profile

GEN_COLS = ("lignite", "nuclear", "wind_offshore", "hydro", "other_conventional",
            "other_renewable", "biomass", "wind_onshore", "solar", "hard_coal", "pumped_hydro",
            "gas")


@dataclass
class Result:
    snapshots: pd.DatetimeIndex
    buses: list[str]
    branches: list[str]
    flow: np.ndarray            # T x branches, MW (sign: bus0 -> bus1)
    loading: np.ndarray         # T x branches, |flow| / s_nom
    injection: np.ndarray       # T x buses, MW (incl. border)
    by_carrier: pd.DataFrame    # T x carrier, MW (producers/storage +, "load" = demand)
    border: pd.DataFrame        # T x border_id, MW (+ = import into DE)
    trade_deviation: np.ndarray  # T, MW import beyond the 2024 net import (keep_trade) or total


def historical_import(ts: pd.DataFrame) -> np.ndarray:
    gen = ts[[c for c in GEN_COLS if c in ts]].fillna(0.0).sum(axis=1)
    return (ts["load"] + ts["pumped_hydro_load"] - gen).to_numpy()


def _carrier_of(a: dict) -> str:
    return a["behaviour"].get("carrier", a["carrier"]) if is_plain_profile(a) else a["carrier"]


def simulate(
    assets: list[dict],
    buses: list[str],
    ptdf: np.ndarray,
    branches: list[str],
    s_nom: np.ndarray,
    borders: pd.DataFrame,
    ctx: Context,
    balancing: str = "keep_trade",
) -> Result:
    if balancing not in ("keep_trade", "border"):
        raise ValueError(balancing)
    T, nb = ctx.n, len(buses)
    bidx = {b: i for i, b in enumerate(buses)}
    inj = np.zeros((T, nb))
    carriers: dict[str, np.ndarray] = {}
    disp_rows: list[np.ndarray] = []
    disp_pmax: list[np.ndarray] = []
    disp_meta: list[tuple[int, str]] = []   # (bus idx, carrier)

    def add_carrier(c: str, x: np.ndarray) -> None:
        carriers[c] = carriers.get(c, 0) + x

    # 1) vectorised plain national profiles: (bus x month capacity) x capacity factors
    plain = [a for a in assets if a["kind"] == "producer" and is_plain_profile(a)]
    for carrier in sorted({_carrier_of(a) for a in plain}):
        cf = ctx.capacity_factor(carrier)
        cap_bm = np.zeros((nb, 12))
        for a in plain:
            if _carrier_of(a) == carrier:
                m = a.get("p_nom_monthly")
                cap_bm[bidx[a["bus"]]] += (np.asarray(m, float) if m is not None and len(m) == 12
                                           else a["p_nom"])
        cap_t = cap_bm[:, ctx.month_idx]                       # buses x T
        if carrier in DISPATCHABLE:
            for i in np.flatnonzero(cap_bm.any(axis=1)):
                disp_rows.append(cap_t[i] * cf)
                disp_pmax.append(cap_t[i])
                disp_meta.append((int(i), carrier))
        else:
            gen = cap_t * cf                                   # buses x T
            inj += gen.T
            add_carrier(carrier, gen.sum(axis=0))

    # 2) everything else, asset by asset
    for a in assets:
        if a["kind"] == "producer" and is_plain_profile(a):
            continue
        x = evaluate(a, ctx)
        i = bidx[a["bus"]]
        c = a["carrier"]
        if a["kind"] == "producer" and c in DISPATCHABLE:
            disp_rows.append(x)
            disp_pmax.append(np.full(T, float(a.get("p_nom") or x.max(initial=0.0))))
            disp_meta.append((i, c))
        elif a["kind"] == "consumer":
            inj[:, i] -= x
            add_carrier("load", x)
        else:  # non-dispatchable producer or storage
            inj[:, i] += x
            add_carrier(c, x)

    # 3) balancing
    disp = np.array(disp_rows).reshape(len(disp_rows), T)
    pmax = np.array(disp_pmax).reshape(len(disp_rows), T)
    target = historical_import(ctx.ts) if balancing == "keep_trade" else np.zeros(T)
    if balancing == "keep_trade" and len(disp_rows):
        surplus = inj.sum(axis=1) + disp.sum(axis=0)          # + = export before balancing
        need = -target - surplus                               # + = more generation needed
        up_room = np.clip(pmax - disp, 0, None)
        for t in range(T):
            d = need[t]
            if d > 0 and (room := up_room[:, t].sum()) > 0:
                disp[:, t] += up_room[:, t] * min(1.0, d / room)
            elif d < 0 and (room := disp[:, t].sum()) > 0:
                disp[:, t] -= disp[:, t] * min(1.0, -d / room)
    for k, (i, c) in enumerate(disp_meta):
        inj[:, i] += disp[k]
        add_carrier(c, disp[k])

    border_total = -inj.sum(axis=1)                            # + = import
    w = borders.capacity_mw.to_numpy() / borders.capacity_mw.sum()
    border = np.outer(border_total, w)
    for k, bus in enumerate(borders.bus):
        inj[:, bidx[bus]] += border[:, k]

    flow = inj @ ptdf.T
    return Result(
        snapshots=ctx.ts.index, buses=list(buses), branches=branches, flow=flow,
        loading=np.abs(flow) / s_nom, injection=inj,
        by_carrier=pd.DataFrame(carriers, index=ctx.ts.index),
        border=pd.DataFrame(border, index=ctx.ts.index, columns=borders.border_id),
        trade_deviation=border_total - target,
    )
