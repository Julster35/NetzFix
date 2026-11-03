"""Simple operator model: minimum-volume redispatch per hour (no costs, no market).

For each snapshot, find bus adjustments that bring every branch within `limit_pu * s_nom`:
  up   <= dispatchable headroom at the bus      (ramp plants up)
  dc   <= dispatchable output at the bus        (ramp plants down)
  dr   <= non-dispatchable output at the bus    (curtail renewables etc.)
  sum(up) = sum(dc) + sum(dr)                   (balance unchanged, trade unchanged)
minimising  sum(up + dc) + res_weight * sum(dr)  + penalty * unresolved overload.
Line constraints are added lazily (only branches that are, or become, overloaded).

This is NOT German redispatch practice (cost-based order, minimum factors for renewables,
reserve plants, countertrading, n-1 security analysis); it is a lower bound on the volume needed
to make the modelled flows feasible, used as a grid-plausibility check (vault: Validation).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import linprog

PENALTY = 1e4


@dataclass
class Redispatch:
    up: np.ndarray            # T x buses, MW
    down_disp: np.ndarray     # T x buses, MW
    down_res: np.ndarray      # T x buses, MW
    flow: np.ndarray          # T x branches, MW after redispatch
    unresolved: np.ndarray    # T, MW of overload that could not be removed (sum over branches)
    limit_pu: float

    def volume_twh(self) -> dict[str, float]:
        up, dd, dr = self.up.sum() / 1e6, self.down_disp.sum() / 1e6, self.down_res.sum() / 1e6
        return {"up": up, "down_dispatchable": dd, "down_curtail": dr, "up_plus_down": up + dd + dr}


def _solve_hour(f0, P, L, up_cap, dd_cap, dr_cap, res_weight, max_iter=25):
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
        c = np.r_[np.ones(nb), np.ones(nb), np.full(nb, res_weight), np.full(2 * nk, PENALTY)]
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
               res_weight: float = 1.0) -> Redispatch:
    T, nb = headroom.shape
    L = limit_pu * s_nom
    up, dd, dr = np.zeros((T, nb)), np.zeros((T, nb)), np.zeros((T, nb))
    unresolved = np.zeros(T)
    flow = flow0.copy()
    for t in range(T):
        if not (np.abs(flow0[t]) > L + 1e-6).any():
            continue
        x, s = _solve_hour(flow0[t], ptdf, L, np.clip(headroom[t], 0, None),
                           np.clip(disp[t], 0, None), np.clip(res[t], 0, None), res_weight)
        up[t], dd[t], dr[t] = x[:nb], x[nb:2 * nb], x[2 * nb:]
        flow[t] = flow0[t] + ptdf @ (up[t] - dd[t] - dr[t])
        unresolved[t] = s
    return Redispatch(up, dd, dr, flow, unresolved, limit_pu)
