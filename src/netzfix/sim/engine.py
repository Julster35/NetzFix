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
Border (A18):
- v1 (if `ts` has columns `xb_<CC>` = measured physical import from country CC, MW, and `borders`
  has `inject_bus`): the 2024 trade target is the measured physical exchange; each country's
  flow is injected at its virtual neighbour bus (AC lines) and its HVDC converter buses, split by
  capacity between those injection points; any deviation caused by edits is spread over countries
  by border capacity.
- v0 fallback: SMARD residual (load + pumped load - generation), split over border points by
  capacity.
Domestic gap: if `ts` has `domestic_gap` (SMARD residual minus measured import, MW) and
`gap_share` is given, it is injected per bus with those shares ("unmetered" generation, + = supply).
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
    border: pd.DataFrame        # T x country (v1) or border_id (v0), MW (+ = import into DE)
    trade_deviation: np.ndarray  # T, MW import beyond the 2024 net import (keep_trade) or total
    res_bus: np.ndarray         # T x buses, MW non-dispatchable generation (curtailable)
    disp_bus: np.ndarray        # T x buses, MW dispatchable generation (can go down)
    headroom_bus: np.ndarray    # T x buses, MW dispatchable headroom (can go up)
    # optional (track_carriers=True): per-carrier T x buses arrays, to attribute redispatch
    res_by_carrier: dict | None = None
    headroom_by_carrier: dict | None = None
    disp_by_carrier: dict | None = None


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
    gap_share: np.ndarray | None = None,
    track_carriers: bool = False,
) -> Result:
    if balancing not in ("keep_trade", "border"):
        raise ValueError(balancing)
    T, nb = ctx.n, len(buses)
    bidx = {b: i for i, b in enumerate(buses)}
    inj = np.zeros((T, nb))
    res_bus = np.zeros((T, nb))
    res_c: dict[str, np.ndarray] = {}
    head_c: dict[str, np.ndarray] = {}
    disp_c: dict[str, np.ndarray] = {}

    def track(store: dict, c: str, i, x) -> None:
        if track_carriers:
            if c not in store:
                store[c] = np.zeros((T, nb))
            if i is None:
                store[c] += x
            else:
                store[c][:, i] += x
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
            reg = (ctx.regional_cf or {}).get(carrier)
            if reg is not None:                                # A27: regional weather
                r = reg.reindex(index=ctx.ts.index, columns=buses).to_numpy(dtype="float64").T
                gen = cap_t * np.where(np.isnan(r), cf[None, :], r)
            else:
                gen = cap_t * cf                               # buses x T
            inj += gen.T
            res_bus += gen.T
            track(res_c, carrier, None, gen.T)
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
            if a["kind"] == "producer":
                res_bus[:, i] += x
                track(res_c, c, i, x)
            add_carrier(c, x)

    # 2b) domestic gap between SMARD balance and measured border flows ("unmetered")
    if gap_share is not None and "domestic_gap" in ctx.ts:
        gap = ctx.ts["domestic_gap"].to_numpy(dtype="float64")
        inj += np.outer(gap, gap_share)
        add_carrier("unmetered_gap", gap)

    # 3) balancing
    xb_cols = [c for c in ctx.ts.columns if c.startswith("xb_")]
    measured = bool(xb_cols) and "inject_bus" in borders
    disp = np.array(disp_rows).reshape(len(disp_rows), T)
    pmax = np.array(disp_pmax).reshape(len(disp_rows), T)
    if balancing == "keep_trade":
        target = (ctx.ts[xb_cols].sum(axis=1).to_numpy() if measured
                  else historical_import(ctx.ts))
    else:
        target = np.zeros(T)
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
    disp_bus = np.zeros((T, nb))
    headroom_bus = np.zeros((T, nb))
    for k, (i, c) in enumerate(disp_meta):
        inj[:, i] += disp[k]
        disp_bus[:, i] += disp[k]
        headroom_bus[:, i] += np.clip(pmax[k] - disp[k], 0, None)
        track(head_c, c, i, np.clip(pmax[k] - disp[k], 0, None))
        track(disp_c, c, i, disp[k])
        add_carrier(c, disp[k])

    border_total = -inj.sum(axis=1)                            # + = import
    if measured:
        cap_c = borders.groupby("country").capacity_mw.sum()
        countries = [c for c in cap_c.index if f"xb_{c}" in ctx.ts]
        cap_c = cap_c[countries]
        base = np.column_stack([ctx.ts[f"xb_{c}"].to_numpy(dtype="float64") for c in countries])
        dev = border_total - base.sum(axis=1)                  # edits / balancing remainder
        flows_c = base + np.outer(dev, (cap_c / cap_c.sum()).to_numpy())
        for j, c in enumerate(countries):
            rows = borders[borders.country == c]
            w_inj = rows.groupby("inject_bus").capacity_mw.sum()
            for ib, cap in w_inj.items():
                inj[:, bidx[ib]] += flows_c[:, j] * cap / w_inj.sum()
        border = pd.DataFrame(flows_c, index=ctx.ts.index, columns=countries)
    else:
        w = borders.capacity_mw.to_numpy() / borders.capacity_mw.sum()
        b_arr = np.outer(border_total, w)
        for k, bus in enumerate(borders.bus):
            inj[:, bidx[bus]] += b_arr[:, k]
        border = pd.DataFrame(b_arr, index=ctx.ts.index, columns=borders.border_id)

    flow = inj @ ptdf.T
    return Result(
        snapshots=ctx.ts.index, buses=list(buses), branches=branches, flow=flow,
        loading=np.abs(flow) / s_nom, injection=inj,
        by_carrier=pd.DataFrame(carriers, index=ctx.ts.index),
        border=border,
        trade_deviation=border_total - target,
        res_bus=res_bus, disp_bus=disp_bus, headroom_bus=headroom_bus,
        res_by_carrier=res_c or None, headroom_by_carrier=head_c or None,
        disp_by_carrier=disp_c or None,
    )
