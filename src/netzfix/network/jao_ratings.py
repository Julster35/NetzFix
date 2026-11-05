"""Line ratings from the JAO Core Static Grid Model (6th release, 2024-09) for the German OSM grid.

Source: vault/data/JAO Core Static Grid Model.md (research use only, Decision Log 2026-11-05).
Rule (pre-registered as v9, assumption A34):
- Circuits of the four German TSOs at 220/380 kV (sheets Lines and Tielines).
- Imax per circuit = `Fixed`, else `DLRmin(A)`, else the minimum over `Period 1-6`.
- Each circuit's end points come from the publication map (straight polyline per EIC code).
  Candidate OSM buses of the same voltage within MATCH_RADIUS_KM of each end; the circuit is the
  shortest same-voltage OSM path between the two candidate sets. Accepted if the path length is
  within LENGTH_TOL of the JAO length (or within LENGTH_ABS_KM for short circuits). If both ends
  were found by OSM substation name, a longer path is allowed (JAO lists only the TSO's share of
  inter-TSO circuits): (1 - LENGTH_TOL) * km - LENGTH_ABS_KM <= path <= max(1.3 km, km + 10).
- Tripods (`Y-X (-A - B)`): the three legs are matched together; the junction is the OSM node
  common to the three pairwise shortest paths whose leg lengths best fit JAO's.
- Per OSM line: s_nom = sum over matched circuits of sqrt(3) * U * Imax, plus the OSM default per
  circuit for circuits that stay unmatched (OSM circuits - matched, if > 0). Unmatched lines keep
  their OSM s_nom.
Writes data/processed/line_ratings_jao.csv and line_ratings_jao_report.json.
"""

from __future__ import annotations

import itertools
import json
import re

import networkx as nx
import numpy as np
import pandas as pd

from netzfix.config import DATA_PROCESSED, DATA_RAW
from netzfix.network import grid as gridmod

SGM_DIR = DATA_RAW / "jao" / "core_sgm_6th"
XLSX = SGM_DIR / "20240916_Core Static Grid Model_for publication.xlsx"
MAP = SGM_DIR / "map" / "2024-09-13_Core_SGM_publication.html"
OUT = DATA_PROCESSED / "line_ratings_jao.csv"
REPORT = DATA_PROCESSED / "line_ratings_jao_report.json"
DE_TSOS = {"50HERTZ", "AMPRION GMBH", "TENNETGMBH", "TRANSNETBW"}
MATCH_RADIUS_KM = 5.0          # around a map coordinate
NAME_RADIUS_KM = 2.0           # around an OSM substation found by name
NAME_SCORE_MIN = 90
NAME_MAX_SHIFT_KM = 40.0       # name hit must lie this close to the (coarse) map coordinate
STOP = re.compile(r"\b(umspannwerk|uw|schaltanlage|schaltwerk|station|substation|transnetbw|"
                  r"amprion|tennet|50hertz|kraftwerk|kw|\d+\s*kv)\b")
LENGTH_TOL = 0.30
LENGTH_ABS_KM = 3.0
NAME_LENGTH_FACTOR = 1.3      # both ends by name: path <= max(1.3 x JAO km, JAO km + 10)
NAME_LENGTH_ABS_KM = 10.0
COLS = ["name", "eic", "tso", "s1", "s2", "kv", "p1", "p2", "p3", "p4", "p5", "p6", "fixed",
        "dlrmin", "dlrmax", "R", "X", "B", "km"]


def imax(d: pd.DataFrame) -> pd.Series:
    """A34: Fixed, else DLRmin, else the lowest seasonal period; NaN if none (DLRmax alone is
    not used: it is the upper band of a temperature-dependent rating)."""
    return d.fixed.fillna(d.dlrmin).fillna(d[["p1", "p2", "p3", "p4", "p5", "p6"]].min(axis=1))


def circuits() -> pd.DataFrame:
    parts = []
    for sheet in ("Lines", "Tielines"):
        d = pd.read_excel(XLSX, sheet_name=sheet, header=1)
        d = d.iloc[:, :len(COLS)]
        d.columns = COLS
        d["sheet"] = sheet
        parts.append(d)
    d = pd.concat(parts, ignore_index=True)
    d = d[d.tso.astype(str).str.strip().isin(DE_TSOS)].copy()
    for c in ["kv", "p1", "p2", "p3", "p4", "p5", "p6", "fixed", "dlrmin", "dlrmax", "km"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["imax_a"] = imax(d)
    d["v"] = np.where(d.kv >= 300, 380.0, 220.0)
    d["eic"] = d.eic.astype(str).str.strip()
    return d[d.kv.between(200, 420)].reset_index(drop=True)


def map_ends() -> dict[str, tuple[float, float, float, float]]:
    """EIC -> (lon0, lat0, lon1, lat1) from the publication map's polylines."""
    s = MAP.read_text(encoding="utf-8")
    m = re.search(r'<script type="application/json" data-for="[^"]+">(.*?)</script>', s, re.S)
    calls = json.loads(m.group(1))["x"]["calls"]
    args = next(c for c in calls if c["method"] == "addPolylines")["args"]
    geoms, popups = args[0], args[4]
    out = {}
    for g, p in zip(geoms, popups, strict=True):
        e = re.search(r"EIC Code:<b>\s*([^<\s]+)", p)
        if not e:
            continue
        pts = g[0][0]
        out[e.group(1).strip()] = (pts["lng"][0], pts["lat"][0], pts["lng"][-1], pts["lat"][-1])
    return out


def _norm(x: str) -> str:
    x = str(x).lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        x = x.replace(a, b)
    x = STOP.sub(" ", x)
    return re.sub(r"[^a-z0-9]+", " ", x).strip()


def osm_substations() -> pd.DataFrame:
    from netzfix.data.osm_line_tags import download_substations

    rows = []
    for p in download_substations():
        for e in json.loads(p.read_text(encoding="utf-8"))["elements"]:
            t = e.get("tags", {})
            c = e.get("center", e)
            if "name" in t and "lat" in c:
                rows.append({"osm": f"{e['type']}/{e['id']}", "name": t["name"],
                             "key": _norm(t["name"]), "lon": c["lon"], "lat": c["lat"]})
    return pd.DataFrame(rows).drop_duplicates("osm")


def locate(name: str, lon: float, lat: float, subs: pd.DataFrame) -> tuple[float, float, str]:
    """(lon, lat, how) of a JAO substation: OSM substation by name near the map point, else the
    map point itself. Y-nodes (tripod points) have no substation and keep the map point."""
    from rapidfuzz import fuzz

    key = _norm(name)
    if key and not str(name).startswith("Y-"):
        near = subs[_km(subs.lon, subs.lat, lon, lat) <= NAME_MAX_SHIFT_KM]
        if len(near):
            sc = near.key.map(lambda k: fuzz.token_set_ratio(key, k))
            hit = near[sc >= NAME_SCORE_MIN]
            if len(hit):
                d = _km(hit.lon, hit.lat, lon, lat)
                h = hit.iloc[int(np.argmin(d))]
                return float(h.lon), float(h.lat), "name"
    return lon, lat, "map"


def _km(lon, lat, lon0, lat0):
    return np.hypot((np.asarray(lat) - lat0) * 111.2,
                    (np.asarray(lon) - lon0) * 111.2 * np.cos(np.radians(lat0)))


def build() -> pd.DataFrame:
    n = gridmod.load().network
    L = n.lines[n.lines.carrier == "AC"].copy()
    B = n.buses
    L["v"] = B.v_nom.reindex(L.bus0).to_numpy()
    circ_osm = L.num_parallel.round().clip(lower=1).astype(int).to_dict()
    graphs = {}
    for v in (220.0, 380.0):
        G = nx.Graph()
        for name, r in L[L.v == v].iterrows():
            if not G.has_edge(r.bus0, r.bus1):
                G.add_edge(r.bus0, r.bus1, length=float(r.length), line=name, parallel=[])
                continue
            e = G[r.bus0][r.bus1]                    # parallel line: keep the shortest as main
            if r.length < e["length"]:
                e["parallel"].append(e["line"])
                e["line"], e["length"] = name, float(r.length)
            else:
                e["parallel"].append(name)
        graphs[v] = G
    C = circuits()
    ends = map_ends()
    subs = osm_substations()
    rows, assign = [], {}

    def bus_set(name, lon, lat, v):
        lon, lat, how = locate(name, lon, lat, subs)
        bv = B[(B.v_nom == v) & B.index.isin(graphs[v].nodes)]
        r = NAME_RADIUS_KM if how == "name" else MATCH_RADIUS_KM
        return list(bv.index[_km(bv.x, bv.y, lon, lat) <= r]), how

    def shortest(G, a, b):
        H = G.copy()
        H.add_edges_from((("_A", x) for x in a), length=0.0)
        H.add_edges_from((("_B", x) for x in b), length=0.0)
        try:
            return nx.shortest_path(H, "_A", "_B", weight="length")[1:-1]
        except nx.NetworkXNoPath:
            return None

    def km_of(G, path):
        return float(sum(G[u][w]["length"] for u, w in itertools.pairwise(path)))

    def length_ok(km, km_jao, by_name):
        if not np.isfinite(km_jao):
            return False
        lo = (1 - LENGTH_TOL) * km_jao - LENGTH_ABS_KM
        if by_name:          # both ends found by name: JAO may list only this TSO's share
            return lo <= km <= max(NAME_LENGTH_FACTOR * km_jao, km_jao + NAME_LENGTH_ABS_KM)
        return abs(km - km_jao) <= max(LENGTH_TOL * km_jao, LENGTH_ABS_KM)

    def put(G, path, i):
        # parallel OSM lines on one bus pair share the circuits: least-filled one first
        for u, w in itertools.pairwise(path):
            cands = [G[u][w]["line"]] + G[u][w].get("parallel", [])
            ln = min(cands, key=lambda x: len(assign.get(x, [])) / circ_osm[x])
            assign.setdefault(ln, []).append(i)

    tri = C.name.astype(str).str.extract(r"^Y-(.+?) \(-(.+?) - (.+?)\)", expand=True)
    C["tri"] = tri.apply(lambda r: None if r.isna().any() else
                         (r.iloc[0].strip(), frozenset(x.strip() for x in r)), axis=1)
    done = set()
    for c in C.itertuples():
        rec = {"eic": c.eic, "name": c.name, "tso": c.tso, "v": c.v, "imax_a": c.imax_a,
               "km_jao": c.km, "status": "", "km_osm": np.nan, "n_lines": 0, "located": ""}
        if c.Index in done:
            continue
        G = graphs[c.v]
        if c.eic not in ends:
            rec["status"] = "no_map_geometry"
        elif not np.isfinite(c.imax_a):
            rec["status"] = "no_imax"
        elif c.tri is not None:
            # tripod: three legs X - junction; match all legs of this Y together
            legs = C[C.tri.map(lambda t, k=c.tri[1]: t is not None and t[1] == k)
                     & (C.tso == c.tso)]
            done.update(legs.index)
            recs = []
            for leg in legs.itertuples():
                recs.append({"eic": leg.eic, "name": leg.name, "tso": leg.tso, "v": leg.v,
                             "imax_a": leg.imax_a, "km_jao": leg.km, "status": "",
                             "km_osm": np.nan, "n_lines": 0, "located": ""})
            sets, ok_all = [], len(legs) == 3
            for leg in legs.itertuples():
                e = ends.get(leg.eic)
                if e is None:
                    ok_all = False
                    break
                bs, how = bus_set(leg.tri[0], (e[0] + e[2]) / 2, (e[1] + e[3]) / 2, leg.v)
                sets.append((bs, how))
            if ok_all and all(bs for bs, _ in sets):
                P = {}
                for i, k in ((0, 1), (0, 2), (1, 2)):
                    P[i, k] = shortest(G, sets[i][0], sets[k][0])
                if all(P.values()):
                    common = set(P[0, 1]) & set(P[0, 2]) & set(P[1, 2])
                    if common:
                        def sub(path, j):        # path from its start to node j
                            return path[:path.index(j) + 1]
                        best, best_err = None, np.inf
                        for j in common:
                            segs = [sub(P[0, 1], j), sub(P[1, 2], j), sub(P[0, 2][::-1], j)]
                            err = sum(abs(km_of(G, sg) - lg.km) for sg, lg in
                                      zip(segs, legs.itertuples(), strict=True))
                            if err < best_err:
                                best, best_err = segs, err
                        for rec_l, sg, lg, (_, how) in zip(recs, best, legs.itertuples(), sets,
                                                          strict=True):
                            km = km_of(G, sg)
                            rec_l.update(km_osm=km, n_lines=len(sg) - 1, located=f"{how}/Y")
                            if not np.isfinite(lg.imax_a):
                                rec_l["status"] = "no_imax"
                            elif len(sg) < 2:
                                rec_l["status"] = "junction_at_substation"
                            elif length_ok(km, lg.km, how == "name"):
                                rec_l["status"] = "matched"
                                put(G, sg, lg.Index)
                            else:
                                rec_l["status"] = "length_mismatch"
                    else:
                        for rec_l in recs:
                            rec_l["status"] = "tripod_no_junction"
                else:
                    for rec_l in recs:
                        rec_l["status"] = "no_path"
            else:
                for rec_l in recs:
                    rec_l["status"] = "tripod_incomplete"
            rows.extend(recs)
            continue
        else:
            lon0, lat0, lon1, lat1 = ends[c.eic]
            a, how0 = bus_set(c.s1, lon0, lat0, c.v)
            b, how1 = bus_set(c.s2, lon1, lat1, c.v)
            rec["located"] = f"{how0}/{how1}"
            if not a or not b:
                rec["status"] = "no_bus_near_end"
            else:
                path = shortest(G, a, b)
                if not path or len(path) < 2:
                    rec["status"] = "no_path"
                else:
                    km = km_of(G, path)
                    rec["km_osm"], rec["n_lines"] = km, len(path) - 1
                    ok = length_ok(km, c.km, how0 == "name" and how1 == "name")
                    rec["status"] = "matched" if ok else "length_mismatch"
                    if ok:
                        put(G, path, c.Index)
        rows.append(rec)
    R = pd.DataFrame(rows)
    out = []
    for name, r in L.iterrows():
        idx = assign.get(name, [])
        circ = max(int(round(r.num_parallel)), 1)
        per = r.s_nom / circ
        if idx:
            s_m = float(sum(np.sqrt(3) * r.v * C.at[i, "imax_a"] / 1000.0 for i in idx))
            s_new = s_m + max(circ - len(idx), 0) * per
        else:
            s_new = r.s_nom
        out.append({"line": name, "v": r.v, "circuits_osm": circ, "n_matched": len(idx),
                    "s_nom_osm": r.s_nom, "s_nom_jao": s_new,
                    "eic": ";".join(C.loc[idx, "eic"]) if idx else ""})
    rated = pd.DataFrame(out)
    rated.to_csv(OUT, index=False)
    m = rated.n_matched > 0
    km = L.length.reindex(rated.line).to_numpy()
    rep = {
        "circuits_de": int(len(R)),
        "circuit_status": R.status.value_counts().to_dict(),
        "status_by_tso_v": {f"{t} {int(v)}": g.status.value_counts().to_dict()
                            for (t, v), g in R.groupby(["tso", "v"])},
        "osm_lines_ac": int(len(rated)), "osm_lines_rated": int(m.sum()),
        "osm_km_rated_share": float(km[m.to_numpy()].sum() / km.sum()),
        "osm_lines_more_circuits_than_osm": int((rated.n_matched > rated.circuits_osm).sum()),
        "s_nom_ratio_median_rated": float((rated.s_nom_jao / rated.s_nom_osm)[m].median()),
        "total_mva_osm_rated": float(rated.s_nom_osm[m].sum()),
        "total_mva_jao_rated": float(rated.s_nom_jao[m].sum()),
    }
    REPORT.write_text(json.dumps(rep, indent=1), encoding="utf-8")
    R.to_csv(DATA_PROCESSED / "line_ratings_jao_circuits.csv", index=False)
    return rated


if __name__ == "__main__":
    build()
    print(REPORT.read_text(encoding="utf-8"))
