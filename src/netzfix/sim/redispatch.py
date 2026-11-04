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

Not modelled (documented in vault Validation): grid switching (comes first in law), grid-reserve
plants (§ 13 Abs. 1c; no reserve units in the asset list), countertrading, the < 100 kW
last-resort rule (§ 13 Abs. 1 S. 3), unit-specific conventional costs (uniform published averages
are used), n-1 security analysis.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import linprog

PENALTY = 1e4


@dataclass
class CostRule:
    """Hourly selection prices, EUR/MWh (arrays of length T)."""
    c_up: np.ndarray      # conventional up (cost)
    c_down: np.ndarray    # conventional down (negative = refund of saved cost)
    p_ee: np.ndarray      # calculated price for curtailing renewables

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
        return cls(pick("c_up"), pick("c_down"), pick("p_ee"))


@dataclass
class Redispatch:
    up: np.ndarray            # T x buses, MW
    down_disp: np.ndarray     # T x buses, MW
    down_res: np.ndarray      # T x buses, MW
    flow: np.ndarray          # T x branches, MW after redispatch
    unresolved: np.ndarray    # T, MW of overload that could not be removed (sum over branches)
    limit_pu: float

    cost_eur: np.ndarray | None = None   # T, selection cost (cost_based rule only)

    def volume_twh(self) -> dict[str, float]:
        up, dd, dr = self.up.sum() / 1e6, self.down_disp.sum() / 1e6, self.down_res.sum() / 1e6
        return {"up": up, "down_dispatchable": dd, "down_curtail": dr, "up_plus_down": up + dd + dr}


def _solve_hour(f0, P, L, up_cap, dd_cap, dr_cap, w_up, w_dc, w_dr, max_iter=25):
    nb = len(up_cap)
    k_set: list[int] = list(np.flatnonzero(np.abs(f0) > L + 1e-6))
    x = np.zeros(3 * nb)
    slack_total = 0.0
    for _ in range(max_iter):
        if not k_set:
            return x, 0.0
        K = np.array(k_set)
        nk = len(K)
        # variables: up(nb) dc(nb) dr(nb) s_plus(nk) s_minus(nk)
        c = np.r_[np.full(nb, w_up), np.full(nb, w_dc), np.full(nb, w_dr),
                  np.full(2 * nk, PENALTY)]
        Pk = P[K]
        A_flow = np.hstack([Pk, -Pk, -Pk])
        A_ub = np.vstack([
            np.hstack([A_flow, -np.eye(nk), np.zeros((nk, nk))]),
            np.hstack([-A_flow, np.zeros((nk, nk)), -np.eye(nk)]),
        ])
        b_ub = np.r_[L[K] - f0[K], L[K] + f0[K]]
        A_eq = np.r_[np.ones(nb), -np.ones(nb), -np.ones(nb), np.zeros(2 * nk)][None, :]
        bounds = ([(0, u) for u in up_cap] + [(0, d) for d in dd_cap]
                  + [(0, r) for r in dr_cap] + [(0, None)] * (2 * nk))
        res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=[0.0], bounds=bounds,
                      method="highs")
        if res.status != 0:
            raise RuntimeError(f"redispatch LP failed: {res.message}")
        x = res.x[: 3 * nb]
        slack_total = float(res.x[3 * nb:].sum())
        delta = x[:nb] - x[nb:2 * nb] - x[2 * nb:]
        f = f0 + P @ delta
        new = [k for k in np.flatnonzero(np.abs(f) > L + 1e-3) if k not in set(k_set)]
        if not new:
            return x, slack_total
        k_set += new
    return x, slack_total


def redispatch(flow0: np.ndarray, ptdf: np.ndarray, s_nom: np.ndarray, headroom: np.ndarray,
               disp: np.ndarray, res: np.ndarray, limit_pu: float = 1.0,
               res_weight: float = 1.0, costs: CostRule | None = None) -> Redispatch:
    """`costs=None`: min_volume rule; otherwise the cost_based rule with these prices."""
    T, nb = headroom.shape
    if costs is not None and (costs.c_up + costs.c_down <= 0).any():
        raise ValueError("c_up + c_down must be > 0, otherwise up/down loops are free")
    cost = np.zeros(T) if costs is not None else None
    L = limit_pu * s_nom
    up, dd, dr = np.zeros((T, nb)), np.zeros((T, nb)), np.zeros((T, nb))
    unresolved = np.zeros(T)
    flow = flow0.copy()
    for t in range(T):
        if not (np.abs(flow0[t]) > L + 1e-6).any():
            continue
        w = ((1.0, 1.0, res_weight) if costs is None
             else (costs.c_up[t], costs.c_down[t], costs.p_ee[t]))
        x, s = _solve_hour(flow0[t], ptdf, L, np.clip(headroom[t], 0, None),
                           np.clip(disp[t], 0, None), np.clip(res[t], 0, None), *w)
        up[t], dd[t], dr[t] = x[:nb], x[nb:2 * nb], x[2 * nb:]
        if cost is not None:
            cost[t] = w[0] * up[t].sum() + w[1] * dd[t].sum() + w[2] * dr[t].sum()
        flow[t] = flow0[t] + ptdf @ (up[t] - dd[t] - dr[t])
        unresolved[t] = s
    return Redispatch(up, dd, dr, flow, unresolved, limit_pu, cost)
