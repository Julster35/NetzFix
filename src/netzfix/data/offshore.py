"""Offshore wind grid connections, reconstructed from data (no hand-made list).

1. MaStR: each operating offshore unit -> its location -> grid connection point(s)
   (`Netzanschlusspunkte`), whose names follow the TSO scheme `L-155-<farm>-<platform>-...`
   (e.g. `L-155-DYSK-SWAL-AC120`); `Nettoengpassleistung` = connection capacity (kW).
2. OpenStreetMap (Overpass API, ODbL): HVDC export cables named BorWin/DolWin/HelWin/SylWin with
   full geometry. Per system: onshore end = cable point closest to a >= 380 kV grid bus;
   offshore end = cable point farthest from that.
3. Matching is purely geographic: each platform group (farms sharing a platform code) goes to the
   system whose offshore end is nearest to the group's capacity-weighted centroid. The platform
   codes are only a cross-check (printed, not used).
Farms without a matched HVDC system (AC-connected and Baltic farms) keep the nearest >= 380 kV bus.
"""

from __future__ import annotations

import json
import re
import zipfile
from collections import defaultdict
from xml.etree.ElementTree import iterparse

import numpy as np
import pandas as pd
import requests

from netzfix.config import DATA_PROCESSED, DATA_RAW
from netzfix.data.download import USER_AGENT, append_manifest
from netzfix.data.mastr import ZIP

OVERPASS = "https://overpass-api.de/api/interpreter"
QUERY = ('[out:json][timeout:120];'
         'way["power"="cable"]["name"~"BorWin|DolWin|HelWin|SylWin",i](52.8,5.5,55.5,9.8);'
         'out tags geom;')
SYSTEM = re.compile(r"(BorWin|DolWin|HelWin|SylWin)\s*(\d)", re.I)
OUT = DATA_PROCESSED / "offshore_connections.csv"
FALLBACK_KM = 15.0


def _rows(z: zipfile.ZipFile, prefix: str, tag: str):
    for n in sorted(x for x in z.namelist() if x.startswith(prefix)):
        with z.open(n) as fh:
            rec: dict = {}
            for _, el in iterparse(fh):
                if el.tag == tag:
                    yield rec
                    rec = {}
                    el.clear()
                else:
                    rec[el.tag] = el.text


def mastr_groups() -> pd.DataFrame:
    """One row per offshore location: farm, platform code, connection MW, capacity, centroid."""
    with zipfile.ZipFile(ZIP) as z:
        units = [r for r in _rows(z, "EinheitenWind", "EinheitWind")
                 if r.get("WindAnLandOderAufSee") == "889"]
        locs = {u.get("LokationMaStRNummer") for u in units} - {None}
        san = [r for r in _rows(z, "Netzanschlusspunkte", "Netzanschlusspunkt")
               if r.get("LokationMaStRNummer") in locs]
    plat: dict[str, str] = {}
    conn: dict[str, float] = defaultdict(float)
    for s in san:
        name = (s.get("NetzanschlusspunktBezeichnung") or "").strip()
        m = re.match(r"L-\d+-(\w{4})-(\w{4})-", name)
        plat[s["LokationMaStRNummer"]] = m.group(2) if m else (name or "unknown")
        conn[s["LokationMaStRNummer"]] += float(s.get("Nettoengpassleistung") or 0) / 1000
    df = pd.DataFrame([{
        "unit": u["EinheitMastrNummer"], "loc": u.get("LokationMaStRNummer"),
        "farm": u.get("NameWindpark"), "mw": float(u.get("Nettonennleistung") or 0) / 1000,
        "lon": float(u.get("Laengengrad") or "nan"), "lat": float(u.get("Breitengrad") or "nan"),
    } for u in units])
    df["platform"] = df["loc"].map(plat).fillna("unknown")
    df["connection_mw_loc"] = df["loc"].map(conn).fillna(0.0)
    return df


def osm_cables() -> list[dict]:
    path = DATA_RAW / "osm_overpass" / "offshore_hvdc_cables.json"
    if not path.exists():
        r = requests.post(OVERPASS, data={"data": QUERY}, timeout=180,
                          headers={"User-Agent": USER_AGENT})
        r.raise_for_status()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(r.content)
        append_manifest(OVERPASS, path, "vault/data/OSM PyPSA-Eur Grid.md", "ODbL-1.0",
                        "Overpass: power=cable named BorWin/DolWin/HelWin/SylWin, out geom")
    return json.loads(path.read_text(encoding="utf-8"))["elements"]


def _km(lon, lat):
    return np.column_stack([np.asarray(lon) * 111.32 * np.cos(np.radians(54.0)),
                            np.asarray(lat) * 110.57])


def systems(ehv: pd.DataFrame) -> pd.DataFrame:
    """Per HVDC system: onshore point, landing bus, offshore end. `ehv`: buses >= 380 kV."""
    pts: dict[str, list] = defaultdict(list)
    for e in osm_cables():
        names = {f"{a.title()}{b}" for a, b in SYSTEM.findall(e.get("tags", {}).get("name", ""))}
        if len(names) != 1:          # shared corridors ("HelWin 1; SylWin 1") are ambiguous
            continue
        pts[names.pop()] += [(g["lon"], g["lat"]) for g in e.get("geometry", [])]
    bxy = _km(ehv.x, ehv.y)
    rows = []
    for name, p in sorted(pts.items()):
        p = np.array(p)
        pk = _km(p[:, 0], p[:, 1])
        d = np.sqrt(((pk[:, None, :] - bxy[None, :, :]) ** 2).sum(-1))       # points x buses
        i, j = np.unravel_index(d.argmin(), d.shape)
        far = np.sqrt(((pk - pk[i]) ** 2).sum(1)).argmax()
        rows.append({"system": name, "landing_bus": ehv.index[j], "landing_dist_km": d[i, j],
                     "on_lon": p[i, 0], "on_lat": p[i, 1],
                     "off_lon": p[far, 0], "off_lat": p[far, 1], "n_points": len(p)})
    return pd.DataFrame(rows)


def build(ehv: pd.DataFrame) -> pd.DataFrame:
    """Unit -> landing bus table, saved to data/processed/offshore_connections.csv."""
    units = mastr_groups()
    sysdf = systems(ehv)
    g = (units.dropna(subset=["lon"]).assign(w=lambda d: d.mw)
         .groupby("platform").apply(lambda d: pd.Series({
             "lon": np.average(d.lon, weights=d.w + 1e-9),
             "lat": np.average(d.lat, weights=d.w + 1e-9), "mw": d.mw.sum(),
             "farms": ", ".join(sorted({f for f in d.farm if f}))}), include_groups=False))
    off = _km(sysdf.off_lon, sysdf.off_lat)
    gk = _km(g.lon, g.lat)
    d = np.sqrt(((gk[:, None, :] - off[None, :, :]) ** 2).sum(-1))
    g["system"] = sysdf.system.to_numpy()[d.argmin(1)]
    g["system_dist_km"] = d.min(1)
    # only HVDC platform groups (TSO code of 4 letters ending in a Greek letter) are matched;
    # AC-connected and Baltic farms keep the nearest >= 380 kV bus
    hvdc = g.index.str.fullmatch(r"(BW|DW|HW|SW)\w\w")
    g.loc[~hvdc, ["system", "system_dist_km"]] = [None, np.nan]
    g = g.join(sysdf.set_index("system")[["landing_bus", "landing_dist_km"]], on="system")
    out = units.join(g[["system", "landing_bus"]], on="platform")
    # North Sea farms without a platform code: match the farm itself to the nearest offshore
    # cable end if it is within FALLBACK_KM
    miss = (out.platform == "unknown") & (out.lon < 9.5) & out.lon.notna()
    if miss.any():
        fc = out[miss].groupby("farm", dropna=False)[["lon", "lat"]].mean()
        dd = np.sqrt(((_km(fc.lon, fc.lat)[:, None, :] - off[None, :, :]) ** 2).sum(-1))
        fc["system"] = np.where(dd.min(1) <= FALLBACK_KM, sysdf.system.to_numpy()[dd.argmin(1)],
                                None)
        fc["system_dist_km"] = dd.min(1)
        fc = fc.join(sysdf.set_index("system")[["landing_bus"]], on="system")
        key = out.loc[miss, "farm"]
        out.loc[miss, "system"] = key.map(fc.system).to_numpy()
        out.loc[miss, "landing_bus"] = key.map(fc.landing_bus).to_numpy()
        fc.to_csv(DATA_PROCESSED / "offshore_farm_fallback.csv")
    out.to_csv(OUT, index=False)
    g.to_csv(DATA_PROCESSED / "offshore_platform_groups.csv")
    sysdf.to_csv(DATA_PROCESSED / "offshore_hvdc_systems.csv", index=False)
    return g


if __name__ == "__main__":
    from netzfix.network import grid as gridmod

    n = gridmod.load().network
    de = n.buses[(n.buses.country == "DE") & (n.buses.v_nom >= 380)]
    g = build(de)
    pd.set_option("display.width", 200)
    print(pd.read_csv(DATA_PROCESSED / "offshore_hvdc_systems.csv").round(3).to_string())
    print(g[["mw", "system", "system_dist_km", "landing_bus", "farms"]].round(1).to_string())
