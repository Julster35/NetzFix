"""Live OSM tags of German 220/380 kV power lines, cables and routes (Overpass API, ODbL 1.0).

Used to check the circuit count of the PyPSA-Eur prebuilt network (v0.7) against the OSM `cables`
and `circuits` tags. One cached JSON with tags only (no geometry).
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.parse import quote

import numpy as np

from netzfix.config import DATA_RAW
from netzfix.data.download import fetch

OVERPASS = "https://overpass-api.de/api/interpreter"
BBOX = "47.2,5.8,55.1,15.1"  # Germany incl. border lines; neighbour ways dropped later
QUERY = (f'[out:json][timeout:300];'
         f'(way["power"~"^(line|cable)$"]["voltage"~"(220000|380000)"]({BBOX});'
         f'relation["route"="power"]["voltage"~"(220000|380000)"]({BBOX}););out tags;')


def download(stamp: str = time.strftime("%Y%m%d")) -> Path:
    return fetch(f"{OVERPASS}?data={quote(QUERY)}",
                 DATA_RAW / "osm_overpass" / f"de_220_380_line_tags_{stamp}.json",
                 source_note="vault/data/OSM PyPSA-Eur Grid.md", license="ODbL-1.0",
                 notes=f"Overpass: bbox {BBOX} ways power=line|cable, route=power "
                       "relations, voltage 220/380 kV, tags only")


def tags(path: Path) -> dict[str, dict]:
    """'way/123' / 'relation/456' -> OSM tags."""
    d = json.loads(path.read_text(encoding="utf-8"))
    return {f"{e['type']}/{e['id']}": e.get("tags", {}) for e in d["elements"]}


if __name__ == "__main__":
    p = download()
    t = tags(p)
    print(p, len(t))



def download_substations(stamp: str = time.strftime("%Y%m%d"), pause_s: float = 10.0) -> list[Path]:
    """Named 220/380 kV substations (centre + tags), Germany's bbox in 3 x 4 tiles (the single
    query returns 502 at overpass-api.de, 2026-11-05). One cached file per tile."""
    lat0, lon0, lat1, lon1 = (float(x) for x in BBOX.split(","))
    lats, lons = np.linspace(lat0, lat1, 5), np.linspace(lon0, lon1, 4)
    out = []
    for i in range(4):
        for k in range(3):
            box = f"{lats[i]:.2f},{lons[k]:.2f},{lats[i + 1]:.2f},{lons[k + 1]:.2f}"
            q = (f'[out:json][timeout:180];'
                 f'nwr["power"="substation"]["voltage"~"(220000|380000)"]({box});out center tags;')
            dest = DATA_RAW / "osm_overpass" / f"de_220_380_substations_{stamp}_{i}{k}.json"
            fresh = not dest.exists()
            out.append(fetch(f"{OVERPASS}?data={quote(q)}", dest,
                             source_note="vault/data/OSM PyPSA-Eur Grid.md", license="ODbL-1.0",
                             notes=f"Overpass: power=substation 220/380 kV, bbox {box}, "
                                   "centre + tags"))
            if fresh:
                time.sleep(pause_s)
    return out
