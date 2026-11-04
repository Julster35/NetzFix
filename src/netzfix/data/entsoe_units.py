"""ENTSO-E actual generation per generation unit (TR 16.1.A), Germany 2024, hourly.

Source: ENTSO-E Transparency Platform File Library (logged-in user, no API token), monthly ZIPs
`data/raw/entsoe/ActualGenerationOutputPerGenerationUnit_16.1.A_r3/YYYY_MM_...zip` with MANIFEST
rows (2026-11-04). Tab-separated, all of Europe. Each German unit appears once per control area
(DE_50HzT, DE_Amprion, DE_TenneT_GER, DE_TransnetBW) and again under the bidding zones DE_LU /
DE_AT_LU; only control-area rows are kept and (unit, timestamp) duplicates dropped. 15-min values
are averaged to the hour (MW). Missing hours stay NaN (no filling here).
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from netzfix.config import DATA_PROCESSED, DATA_RAW

DATASET = "ActualGenerationOutputPerGenerationUnit_16.1.A_r3"
CONTROL_AREAS = ("DE_50HzT", "DE_Amprion", "DE_TenneT_GER", "DE_TransnetBW")
COLS = ["DateTime(UTC)", "ResolutionCode", "AreaMapCode", "GenerationUnitCode",
        "GenerationUnitName", "GenerationUnitType", "ActualGenerationOutput[MW]"]
OUT = DATA_PROCESSED / "entsoe_units_DE_2024.parquet"
META = DATA_PROCESSED / "entsoe_units_DE_2024_meta.csv"


def _read_month(path: Path) -> pd.DataFrame:
    z = zipfile.ZipFile(path)
    parts = []
    for ch in pd.read_csv(z.open(z.namelist()[0]), sep="\t", usecols=COLS, chunksize=2_000_000):
        parts.append(ch[ch["AreaMapCode"].isin(CONTROL_AREAS)])
    return pd.concat(parts)


def build(year: int = 2024) -> tuple[pd.DataFrame, pd.DataFrame]:
    files = sorted((DATA_RAW / "entsoe" / DATASET).glob(f"{year}_??_{DATASET}.zip"))
    if len(files) != 12:
        raise FileNotFoundError(f"expected 12 monthly files for {year}, found {len(files)}")
    raw = pd.concat(_read_month(f) for f in files)
    raw = raw.drop_duplicates(["GenerationUnitCode", "DateTime(UTC)", "ResolutionCode"])
    raw["time"] = pd.to_datetime(raw["DateTime(UTC)"], utc=True).dt.floor("h")
    mw = raw.groupby(["time", "GenerationUnitCode"])["ActualGenerationOutput[MW]"].mean()
    wide = mw.unstack("GenerationUnitCode")
    idx = pd.date_range(f"{year}-01-01", f"{year + 1}-01-01", freq="h", tz="UTC", inclusive="left")
    wide = wide.reindex(idx)
    meta = (raw.groupby("GenerationUnitCode")
            .agg(name=("GenerationUnitName", "first"), type=("GenerationUnitType", "first"),
                 area=("AreaMapCode", "first"),
                 p_max_obs=("ActualGenerationOutput[MW]", "max"))
            .reset_index().rename(columns={"GenerationUnitCode": "code"}))
    meta["twh"] = meta["code"].map(wide.sum() / 1e6)
    meta["hours_missing"] = meta["code"].map(wide.isna().sum())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    wide.to_parquet(OUT)
    meta.to_csv(META, index=False, encoding="utf-8")
    return wide, meta



# ------------------------------------------------------------------ link to MaStR assets (A26)
PGU = "ProductionAndGenerationUnits_r3.1"
LINKS = DATA_PROCESSED / "entsoe_unit_links_DE_2024.csv"
THERMAL = ("Fossil Brown coal/Lignite", "Fossil Hard coal", "Fossil Gas", "Fossil Coal-derived gas",
           "Fossil Oil")


def _norm(s: str) -> str:
    import re

    s = str(s).lower()
    for a, b in (("ß", "ss"), ("ä", "ae"), ("ö", "oe"), ("ü", "ue")):
        s = s.replace(a, b)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(r"\b(kw|hkw|gkw|kraftwerk|block|gud|kwk|heizkraftwerk|anlage|unit)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _asset_area(assets: pd.DataFrame, tso_by_nuts1: dict[str, str]) -> pd.Series:
    """Control area of each asset from the NUTS-1 region containing its coordinates."""
    from shapely.geometry import Point, shape
    from shapely.strtree import STRtree

    from netzfix.data.regions import geometries

    feats = geometries(2024)
    geoms = [shape(f["geometry"]) for f in feats.values()]
    codes = list(feats)
    tree = STRtree(geoms)
    out = {}
    for r in assets.dropna(subset=["lon", "lat"]).itertuples():
        pt = Point(r.lon, r.lat)
        hit = [codes[i] for i in tree.query(pt) if geoms[i].covers(pt)]
        if hit:
            out[r.id] = tso_by_nuts1.get(hit[0][:3])
    return pd.Series(out, dtype=object)


def link(assets: pd.DataFrame, cfg: dict | None = None) -> pd.DataFrame:
    """Link thermal ENTSO-E generation units to baseline MaStR assets.

    1. generation unit -> production unit (ENTSO-E unit master file)
       -> powerplantmatching v0.9.1 entry with that EIC -> its MaStR unit numbers -> assets.
    2. fallback for units still unlinked: name similarity >= NAME_MIN_SCORE (rapidfuzz
       token_set_ratio on normalised names) among unlinked assets of a matching carrier with
       0.5-2x the unit's observed maximum.
    The replay group is the production unit: all its generation units' output is shared over
    its linked assets in proportion to p_nom.
    """
    import re

    from rapidfuzz import fuzz

    from netzfix.config import load_config

    cfg = cfg or load_config()["entsoe_units"]
    meta = pd.read_csv(META)
    meta = meta[meta["type"].isin(THERMAL)].copy()
    z = zipfile.ZipFile(next((DATA_RAW / "entsoe" / PGU).glob("*.zip")))
    u = pd.read_csv(z.open(z.namelist()[0]), sep="\t",
                    usecols=["GenerationUnitCode", "ProductionUnitCode", "AreaMapCode"])
    u = u[u["AreaMapCode"].astype(str).str.startswith("DE")]
    meta["group"] = meta["code"].map(
        u.drop_duplicates("GenerationUnitCode").set_index("GenerationUnitCode")
        ["ProductionUnitCode"])
    ppm = pd.read_csv(DATA_RAW / "ppm" / "powerplants_v0.9.1.csv",
                      usecols=["Country", "EIC", "projectID"])
    ppm = ppm[ppm["Country"] == "Germany"]
    eic = re.compile(r"'([0-9]{2}W[0-9A-Z\-]{13})'")
    see = re.compile(r"MASTR-(SEE\d+)")
    pu2see: dict[str, set[str]] = {}
    for r in ppm.itertuples():
        for e in set(eic.findall(str(r.EIC)) + eic.findall(str(r.projectID))):
            pu2see.setdefault(e, set()).update(see.findall(str(r.projectID)))
    ids = set(assets["id"])
    meta["assets"] = meta["group"].map(
        lambda g: sorted(f"mastr/{s}" for s in pu2see.get(g, ()) if f"mastr/{s}" in ids)
        if isinstance(g, str) else [])
    # conflicts: one asset claimed by several production units (powerplantmatching merges)
    area_of = _asset_area(assets, cfg["tso_by_nuts1"])
    claims = meta[meta["assets"].map(len) > 0].groupby("group").agg(
        assets=("assets", "first"), area=("area", "first"))
    ex = claims["assets"].explode()
    multi = ex[ex.duplicated(keep=False)]
    drop = set()                                   # (group, asset) pairs to remove
    for aid, grps in multi.reset_index().groupby("assets")["group"]:
        a_area = area_of.get(aid)
        keep = [g for g in grps if claims.at[g, "area"] == a_area]
        if keep:                                   # area decides; else keep all (merged below)
            drop |= {(g, aid) for g in grps if g not in keep}
    meta["assets"] = [[a for a in lst if (g, a) not in drop]
                      for g, lst in zip(meta["group"], meta["assets"], strict=True)]
    # remaining overlaps (same area, same site): merge the production units into one group
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        while parent.get(x, x) != x:
            x = parent[x]
        return x
    owner: dict[str, str] = {}
    for g, lst in zip(meta["group"], meta["assets"], strict=True):
        for a in lst:
            if a in owner and find(owner[a]) != find(g):
                parent[find(g)] = find(owner[a])
            owner.setdefault(a, g)
    meta["group"] = [find(g) if isinstance(g, str) else g for g in meta["group"]]
    merged = meta.groupby("group")["assets"].apply(lambda s: sorted({a for x in s for a in x}))
    meta["assets"] = [merged.get(g, []) if lst else [] for g, lst in
                      zip(meta["group"], meta["assets"], strict=True)]
    # site check: drop assets far from the group's median location (ppm name-merges across
    # cities); only for groups with >= 3 assets, so that a majority defines the site
    loc = assets.set_index("id")[["lat", "lon"]]
    km = 111.0
    for g in meta["group"].dropna().unique():
        lst = merged.get(g, [])
        if len(lst) < 3:
            continue
        ll = loc.loc[lst].dropna()
        mlat, mlon = ll["lat"].median(), ll["lon"].median()
        d = np.hypot((ll["lat"] - mlat) * km, (ll["lon"] - mlon) * km * np.cos(np.radians(mlat)))
        far = set(d[d > cfg["max_site_km"]].index)
        if far:
            merged[g] = [a for a in lst if a not in far]
            meta["assets"] = [merged[g] if gg == g and lst2 else lst2
                              for gg, lst2 in zip(meta["group"], meta["assets"], strict=True)]
    meta["method"] = meta["assets"].map(lambda a: "eic" if a else "")
    taken = {a for lst in meta["assets"] for a in lst}
    cand = assets[(assets["kind"] == "producer")
                  & assets["carrier"].isin(("lignite", "hard_coal", "gas", "other_conventional"))
                  & ~assets["id"].isin(taken)].copy()
    cand["n"] = cand["name"].map(_norm)
    for i in meta.index[meta["method"] == ""]:
        r = meta.loc[i]
        c = cand[(cand["p_nom"] >= 0.5 * r.p_max_obs) & (cand["p_nom"] <= 2.0 * r.p_max_obs)
                 & ~cand["id"].isin(taken)]
        if c.empty:
            continue
        nm = _norm(r["name"])
        sc = c["n"].map(lambda x, nm=nm: fuzz.token_set_ratio(nm, x))
        if sc.max() >= cfg["name_min_score"]:
            j = sc.idxmax()
            meta.at[i, "assets"] = [c.at[j, "id"]]
            meta.at[i, "method"] = f"name:{sc.max():.0f}"
            meta.at[i, "group"] = r["code"]          # own group: not shared with the plant
            taken.add(c.at[j, "id"])
    meta["assets"] = meta["assets"].map(";".join)
    meta.to_csv(LINKS, index=False, encoding="utf-8")
    return meta


if __name__ == "__main__":
    w, m = build()
    print(w.shape, m.groupby("type").twh.sum().round(2).to_dict())
