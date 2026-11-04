"""Operator model: redispatch per hour on DC flows, by one of two selection rules.

For each snapshot, find bus adjustments that bring every branch within `limit_pu * s_nom`:
  up   <= dispatchable headroom at the bus      (ramp plants up)
  dc   <= dispatchable output at the bus        (ramp plants down)
  dr   <= non-dispatchable output at the bus    (curtail renewables etc.)
  sum(up) = sum(dc) + sum(dr)                   (balance unchanged, trade unchanged)
Line constraints are added lazily (only branches that are, or become, overloaded).

Rules (objective; + penalty * unresolved overload in both):
- "min_volume" (v0-v2): sum(up + dc) + res_weight * sum(dr). A lower bound on the volume.
- "cost_based" (v3, assumption A25): sum(c_up*up + c_down*dc + p_ee*dr) with hourly prices from
  `CostRule`. This is the selection rule of § 13 Abs. 1 S. 2 and Abs. 1a EnWG: least total cost,
  conventional plants at cost (c_down < 0: saved fuel is refunded, § 13a Abs. 2), renewables
  (all non-dispatchable producers here are EEG plants) at the uniform calculated price p_ee that
  encodes the minimum factor. Sources: vault/literature "EnWG 13 13a Redispatch",
  "BNetzA 2020 Mindestfaktor-Festlegung", "netztransparenz Kalkulatorische Preise".

Grid-reserve units (A32, optional `reserve` headroom): an extra upward block priced at the
calculated grid-reserve price p_nr (§ 13 Abs. 1c), so they are used after market plants.
Not modelled (documented in vault Validation): grid switching (comes first in law),
countertrading, the < 100 kW last-resort rule (§ 13 Abs. 1 S. 3), unit-specific conventional
costs (uniform published averages are used), n-1 security analysis.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import linprog

PENALTY = 1e4          # min_volume rule (v0-v2, unchanged)
# cost_based rule: line security is mandatory (§ 13 Abs. 1 EnWG), cost only chooses the measures.
# The penalty must exceed the cost of relieving 1 MW through any useful plant: renewable pair
# ~800 EUR/MWh / PTDF sensitivity 1e-3 ~ 8e5. With 1e4 the LP left overloads instead (v3 grid
# 5735); 1e8 made HiGHS fail numerically (grid 5742). 1e6 keeps the cost ratio near min_volume's.
PENALTY_COST = 1e6


@dataclass
class CostRule:
    """Hourly selection prices, EUR/MWh (arrays of length T)."""
    c_up: np.ndarray      # conventional up (cost)
    c_down: np.ndarray    # conventional down (negative = refund of saved cost)
    p_ee: np.ndarray      # calculated price for curtailing renewables
    p_nr: np.ndarray | None = None   # calculated price for grid-reserve units (§ 13 Abs. 1c)

    @classmethod
    def from_config(cls, index, periods: list[dict]) -> CostRule:
        """Pick, for every snapshot, the price row whose `valid_from` (local date, Europe/Berlin,
        00:00) is the latest one not after the snapshot."""
        import pandas as pd

        rows = sorted(periods, key=lambda r: str(r["valid_from"]))
        starts = pd.DatetimeIndex([pd.Timestamp(str(r["valid_from"]), tz="Europe/Berlin")
                                   for r in rows])
        idx = pd.DatetimeIndex(index)
        idx = idx.tz_localize("UTC") if idx.tz is None else idx
        k = starts.searchsorted(idx.tz_convert("Europe/Berlin"), side="right") - 1
        if (k < 0).any():
            raise ValueError("snapshots before the first redispatch price period")
        pick = lambda key: np.array([float(rows[i][key]) for i in k])  # noqa: E731
        return cls(pick("c_up"), pick("c_down"), pick("p_ee"), pick("p_nr"))


@dataclass
class Redispatch:
    up: np.ndarray            # T x buses, MW
    down_disp: np.ndarray     # T x buses, MW
    down_res: np.ndarray      # T x buses, MW
    flow: np.ndarray          # T x branches, MW after redispatch
    unresolved: np.ndarray    # T, MW of overload that could not be removed (sum over branches)
    limit_pu: float

    cost_eur: np.ndarray | None = None   # T, selection cost (cost_based rule only)
    up_reserve: np.ndarray | None = None  # T x buses, MW from grid-reserve units (A32)

    def volume_twh(self) -> dict[str, float]:
        up, dd, dr = self.up.sum() / 1e6, self.down_disp.sum() / 1e6, self.down_res.sum() / 1e6
        return {"up": up, "down_dispatchable": dd, "down_curtail": dr, "up_plus_down": up + dd + dr}


def _solve_hour(f0, P, L, caps, weights, signs, penalty=PENALTY, max_iter=25):
    """One hour. Blocks b (each nb variables): cap[b] bounds, weight[b] cost, sign[b] +1 for
    injection increase (up, reserve up), -1 for decrease (conventional down, curtailment).
    Balance: sum over blocks of sign * x = 0."""
    nb = len(caps[0])
    nbl = len(caps)
    k_set: list[int] = list(np.flatnonzero(np.abs(f0) > L + 1e-6))
    x = np.zeros(nbl * nb)
    slack_total = 0.0
    for _ in range(max_iter):
        if not k_set:
            return x, 0.0
        K = np.array(k_set)
        nk = len(K)
        c = np.r_[np.concatenate([np.full(nb, w) for w in weights]), np.full(2 * nk, penalty)]
        Pk = P[K]
        A_flow = np.hstack([sg * Pk for sg in signs])
        A_ub = np.vstack([
            np.hstack([A_flow, -np.eye(nk), np.zeros((nk, nk))]),
            np.hstack([-A_flow, np.zeros((nk, nk)), -np.eye(nk)]),
        ])
        b_ub = np.r_[L[K] - f0[K], L[K] + f0[K]]
        A_eq = np.r_[np.concatenate([np.full(nb, float(sg)) for sg in signs]),
                     np.zeros(2 * nk)][None, :]
        bounds = [(0, v) for cap in caps for v in cap] + [(0, None)] * (2 * nk)
        res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=[0.0], bounds=bounds,
                      method="highs")
        if res.status != 0:
            raise RuntimeError(f"redispatch LP failed: {res.message}")
        x = res.x[: nbl * nb]
        slack_total = float(res.x[nbl * nb:].sum())
        delta = sum(sg * x[b * nb:(b + 1) * nb] for b, sg in enumerate(signs))
        f = f0 + P @ delta
        new = [k for k in np.flatnonzero(np.abs(f) > L + 1e-3) if k not in set(k_set)]
        if not new:
            return x, slack_total
        k_set += new
    return x, slack_total


def redispatch(flow0: np.ndarray, ptdf: np.ndarray, s_nom: np.ndarray, headroom: np.ndarray,
               disp: np.ndarray, res: np.ndarray, limit_pu: float = 1.0,
               res_weight: float = 1.0, costs: CostRule | None = None,
               reserve: np.ndarray | None = None) -> Redispatch:
    """`costs=None`: min_volume rule; otherwise the cost_based rule with these prices."""
    T, nb = headroom.shape
    if costs is not None and (costs.c_up + costs.c_down <= 0).any():
        raise ValueError("c_up + c_down must be > 0, otherwise up/down loops are free")
    cost = np.zeros(T) if costs is not None else None
    L = limit_pu * s_nom
    up, dd, dr = np.zeros((T, nb)), np.zeros((T, nb)), np.zeros((T, nb))
    ur = np.zeros((T, nb))
    if reserve is not None and costs is not None and costs.p_nr is None:
        raise ValueError("grid-reserve units given but no reserve price (p_nr)")
    unresolved = np.zeros(T)
    flow = flow0.copy()
    for t in range(T):
        if not (np.abs(flow0[t]) > L + 1e-6).any():
            continue
        w = ((1.0, 1.0, res_weight) if costs is None
             else (costs.c_up[t], costs.c_down[t], costs.p_ee[t]))
        caps = [np.clip(headroom[t], 0, None), np.clip(disp[t], 0, None),
                np.clip(res[t], 0, None)]
        signs = [1, -1, -1]
        if reserve is not None:          # A32: grid reserve, after market plants (§ 13 Abs. 1c)
            caps.append(np.clip(reserve[t], 0, None))
            w = (*w, 1.0 if costs is None else costs.p_nr[t])
            signs.append(1)
        x, s = _solve_hour(flow0[t], ptdf, L, caps, list(w), signs,
                           penalty=PENALTY if costs is None else PENALTY_COST)
        up[t], dd[t], dr[t] = x[:nb], x[nb:2 * nb], x[2 * nb:3 * nb]
        if reserve is not None:
            ur[t] = x[3 * nb:4 * nb]
        if cost is not None:
            cost[t] = sum(w[b] * x[b * nb:(b + 1) * nb].sum() for b in range(len(caps)))
        flow[t] = flow0[t] + ptdf @ (up[t] + ur[t] - dd[t] - dr[t])
        unresolved[t] = s
    return Redispatch(up, dd, dr, flow, unresolved, limit_pu, cost,
                      ur if reserve is not None else None)
