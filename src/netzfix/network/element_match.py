"""Match BNetzA overloaded-element names to model branches (assumption A36, test T7).

Rule (pre-registered in vault/project/Validation.md, T7):
1. Each element is a list of substation chains (config/bnetza_elements.yaml).
2. Each substation name -> OSM 220/380 kV substations whose normalised name matches with
   rapidfuzz token_set_ratio >= NAME_SCORE_MIN (normaliser of A34, "sankt" -> "st"). A site
   counts only if a model bus lies within NAME_RADIUS_KM of it.
3. Homonyms: per chain, the combination of sites with the shortest straight-line chain length.
4. Each consecutive pair -> the shortest model path (lines by length, transformers 0 km) between
   the buses of the two sites. Accepted if path km <= max(PATH_FACTOR x straight km,
   straight km + PATH_ABS_KM).
   A pair "A - @CC" (border leg whose foreign station is not in the OSM 220/380 kV query, e.g.
   400 kV in FR/PL) -> shortest path from A to any model bus in country CC, same length rule
   with the straight distance to the nearest CC bus.
   A name that is not found leaves its two pairs unmatched; the other pairs of the chain are
   still matched.
5. The element's branches = union of its accepted paths. Elements with no accepted pair are
   reported and left out of T7.
"""

from __future__ import annotations

import itertools
import re
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
import yaml

from netzfix.config import REPO_ROOT
from netzfix.network.jao_ratings import _km, _norm, osm_substations

CONFIG = REPO_ROOT / "config" / "bnetza_elements.yaml"
NAME_SCORE_MIN = 90
NAME_RADIUS_KM = 2.0
PATH_FACTOR = 2.0
PATH_ABS_KM = 20.0
MAX_SITES = 12
SUBSTATION_STAMP = "20261105"   # same Overpass snapshot as the JAO matching (A34)


def key(name: str) -> str:
    """Join key for published names: drop umlauts and U+FFFD alike (the files lose umlauts)."""
    s = str(name).lower()
    s = re.sub(r"[äöüß�]", "", s)
    return re.sub(r"[^a-z0-9]+", "", s)


def _skey(name: str) -> str:
    name = str(name).replace("ł", "l").replace("Ł", "L")
    return re.sub(r"\bsankt\b", "st", _norm(name))


def load_elements(path: Path = CONFIG) -> dict[str, dict]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))["elements"]


def element_of_name() -> dict[str, str]:
    return {key(n): eid for eid, e in load_elements().items() for n in e["names"]}


def build_graph(n) -> nx.MultiGraph:
    G = nx.MultiGraph()
    for name, r in n.lines.iterrows():
        G.add_edge(r.bus0, r.bus1, branch=f"Line:{name}", km=float(r.length))
    for name, r in n.transformers.iterrows():
        G.add_edge(r.bus0, r.bus1, branch=f"Transformer:{name}", km=0.0)
    return G


def _simple(G: nx.MultiGraph) -> nx.Graph:
    H = nx.Graph()
    for u, w, d in G.edges(data=True):
        if not H.has_edge(u, w) or d["km"] < H[u][w]["km"]:
            H.add_edge(u, w, km=d["km"])
    return H


def match(n, branches: list[str]) -> tuple[dict[str, list[str]], pd.DataFrame]:
    """Returns {element_id: [branch names in `branches`]} and a per-pair report."""
    from rapidfuzz import fuzz

    subs = osm_substations(SUBSTATION_STAMP)
    subs["skey"] = subs.name.map(_skey)
    B = n.buses
    G = build_graph(n)
    H = _simple(G)
    bset = set(branches)

    def sites(name: str) -> list[tuple[float, float, list[str], str]]:
        k = _skey(name)
        hit = subs[subs.skey.map(lambda s: fuzz.token_set_ratio(k, s)) >= NAME_SCORE_MIN]
        out = []
        for _, s in hit.iterrows():
            near = B.index[_km(B.x, B.y, s.lon, s.lat) <= NAME_RADIUS_KM]
            near = [b for b in near if b in H]
            if near:
                out.append((float(s.lon), float(s.lat), near, s["name"]))
        # one site per distinct location (OSM often maps a substation twice)
        uniq, seen = [], set()
        for s in out:
            tag = (round(s[0], 2), round(s[1], 2))
            if tag not in seen:
                seen.add(tag)
                uniq.append(s)
        return uniq[:MAX_SITES]

    def path(a: list[str], b: list[str]):
        Hx = H.copy()
        Hx.add_edges_from((("_A", x) for x in a), km=0.0)
        Hx.add_edges_from((("_B", x) for x in b), km=0.0)
        try:
            p = nx.shortest_path(Hx, "_A", "_B", weight="km")[1:-1]
        except nx.NetworkXNoPath:
            return None, np.inf
        return p, float(sum(Hx[u][w]["km"] for u, w in itertools.pairwise(p)))

    def edges_on(p: list[str]) -> list[str]:
        out = []
        for u, w in itertools.pairwise(p):
            out += [d["branch"] for d in G.get_edge_data(u, w).values() if d["branch"] in bset]
        return out

    result, rows = {}, []
    for eid, e in load_elements().items():
        brs: set[str] = set()
        if not e["chains"]:
            rows.append({"element": eid, "pair": "", "status": "no end points in name"})
        for chain in e["chains"]:
            cand = {s: sites(s) for s in chain if not s.startswith("@")}
            fixed = [s for s in chain if not s.startswith("@") and cand[s]]
            best = {}
            if fixed:
                combo = min(itertools.product(*(cand[s] for s in fixed)),
                            key=lambda c: sum(float(_km(x[0], x[1], y[0], y[1]))
                                              for x, y in itertools.pairwise(c)))
                best = dict(zip(fixed, combo, strict=True))
            for a, b in itertools.pairwise(chain):
                miss = [x for x in (a, b) if not x.startswith("@") and x not in best]
                if miss:
                    rows.append({"element": eid, "pair": f"{a} - {b}",
                                 "status": "substation not found: " + ", ".join(miss)})
                    continue
                if b.startswith("@") or a.startswith("@"):
                    home, cc = (best[a], b[1:]) if b.startswith("@") else (best[b], a[1:])
                    fb = B[(B.country == cc) & B.index.isin(H.nodes)]
                    if fb.empty:
                        rows.append({"element": eid, "pair": f"{a} - {b}",
                                     "status": f"no model bus in {cc}"})
                        continue
                    straight = float(np.min(_km(fb.x, fb.y, home[0], home[1])))
                    sa, sb = home, (None, None, list(fb.index), f"model buses {cc}")
                else:
                    sa, sb = best[a], best[b]
                    straight = float(_km(sa[0], sa[1], sb[0], sb[1]))
                p, km = path(sa[2], sb[2])
                ok = p is not None and km <= max(PATH_FACTOR * straight, straight + PATH_ABS_KM)
                br = edges_on(p) if ok else []
                rows.append({"element": eid, "pair": f"{a} - {b}", "osm_a": sa[3],
                             "osm_b": sb[3], "straight_km": round(straight, 1),
                             "path_km": round(km, 1) if np.isfinite(km) else None,
                             "n_branches": len(br),
                             "status": "matched" if ok and br else
                                       ("same bus" if ok else "path too long / no path")})
                brs.update(br)
        if brs:
            result[eid] = sorted(brs)
    return result, pd.DataFrame(rows)
