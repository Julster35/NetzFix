"""German NUTS3 regions with population, for regionalising demand (assumption A12, v0).

- Geometries: Eurostat GISCO NUTS, 1:1M, EPSG:4326 (licence: (c) EuroGeographics for the
  administrative boundaries, GISCO terms).
- Population on 1 January: Eurostat dataset demo_r_pjanaggr3 (JSON-stat API).
Both read 2026-11-03 (HTTP 200). The NUTS version is chosen so that all DE codes match.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import requests
from shapely.geometry import shape

from netzfix.config import DATA_PROCESSED, DATA_RAW
from netzfix.data.download import USER_AGENT, append_manifest, fetch

GISCO = "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_01M_{v}_4326_LEVL_3.geojson"
EUROSTAT = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/demo_r_pjanaggr3"


def geometries(nuts_version: int) -> dict[str, dict]:
    path = fetch(GISCO.format(v=nuts_version), DATA_RAW / "gisco" / f"NUTS3_{nuts_version}.geojson",
                 source_note="vault/data/DemandRegio.md", license="(c) EuroGeographics / GISCO",
                 notes=f"NUTS {nuts_version} level 3, 1:1M, EPSG:4326")
    fc = json.loads(Path(path).read_text(encoding="utf-8"))
    return {f["properties"]["NUTS_ID"]: f for f in fc["features"]
            if f["properties"]["CNTR_CODE"] == "DE"}


def population(year: int) -> pd.Series:
    path = DATA_RAW / "eurostat" / f"demo_r_pjanaggr3_DE_{year}.json"
    url = f"{EUROSTAT}?sex=T&age=TOTAL&time={year}&format=JSON&lang=EN"
    if not path.exists():
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=120)
        r.raise_for_status()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(r.content)
        append_manifest(url, path, "vault/data/DemandRegio.md", "Eurostat (CC BY 4.0)",
                        f"population 1 Jan {year}, all NUTS3")
    d = json.loads(path.read_text(encoding="utf-8"))
    geo_index = d["dimension"]["geo"]["category"]["index"]  # code -> position
    size = d["size"]
    ids = d["id"]
    # all non-geo dimensions have size 1 here, so the flat index equals the geo position
    assert all(size[i] == 1 for i, k in enumerate(ids) if k != "geo"), size
    vals = {code: d["value"].get(str(pos)) for code, pos in geo_index.items()}
    s = pd.Series(vals, dtype="float64")
    return s[s.index.str.match(r"^DE\w{3}$")].dropna()


LAU = "https://gisco-services.ec.europa.eu/distribution/v2/lau/geojson/LAU_RG_01M_{y}_4326.geojson"


def lau_points(year: int = 2024) -> pd.DataFrame:
    """German municipalities (LAU): id, name, representative point (lon, lat).

    Used to place MaStR units that have no coordinates (small units) by their Gemeindeschluessel.
    """
    out = DATA_PROCESSED / f"lau_DE_{year}_points.parquet"
    if out.exists():
        return pd.read_parquet(out)
    path = fetch(LAU.format(y=year), DATA_RAW / "gisco" / f"LAU_{year}.geojson",
                 source_note="vault/data/Marktstammdatenregister.md",
                 license="(c) EuroGeographics / GISCO", notes=f"LAU {year}, 1:1M, EPSG:4326")
    fc = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = []
    for f in fc["features"]:
        p = f["properties"]
        if p.get("CNTR_CODE") != "DE":
            continue
        pt = shape(f["geometry"]).representative_point()
        rows.append({"lau_id": p["GISCO_ID"].removeprefix("DE_"), "name": p.get("LAU_NAME"),
                     "population": p.get(f"POP_{year}"), "lon": pt.x, "lat": pt.y})
    df = pd.DataFrame(rows)
    df.to_parquet(out)
    return df


def build(year: int = 2024) -> Path:
    pop = population(year)
    for v in (2024, 2021):
        geoms = geometries(v)
        missing = set(pop.index) ^ set(geoms)
        if not missing:
            break
        print(f"NUTS {v}: {len(missing)} codes do not match, trying next version")
    else:
        raise RuntimeError(f"no NUTS version matches population codes: {sorted(missing)[:10]}")
    rows = [{"nuts3": c, "name": geoms[c]["properties"]["NUTS_NAME"], "population": pop[c],
             "wkt": shape(geoms[c]["geometry"]).wkt} for c in sorted(pop.index)]
    out = DATA_PROCESSED / f"nuts3_DE_pop{year}.parquet"
    pd.DataFrame(rows).assign(nuts_version=v).to_parquet(out)
    print(f"NUTS {v}: {len(rows)} regions, population {pop.sum() / 1e6:.2f} M")
    return out


if __name__ == "__main__":
    print(build())
