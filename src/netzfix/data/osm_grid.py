"""PyPSA-Eur prebuilt OSM transmission network (Zenodo, ODbL 1.0).

Version 0.7 (Zenodo record 18619025, 2026-02-12) is the latest version supported by the pinned
PyPSA-Eur release v2026.09.0 (its data/versions.csv, read 2026-11-03). v0.8 exists (2026-11-02) but
is not yet supported by that release.
"""

from __future__ import annotations

from pathlib import Path

from netzfix.config import DATA_RAW
from netzfix.data.download import fetch

RECORD = "18619025"
VERSION = "0.7"
FILES = {  # name -> md5 published by Zenodo
    "buses.csv": "031c30f04dc24e99210b3f5ad8a01c94",
    "lines.csv": "04d1e7cb33835de9c7d8be4716c6a8bf",
    "links.csv": "2ddd515a30cfc19205e6681def579fbd",
    "transformers.csv": "b6730b52097d2691d49231bdd53c7bd4",
    "converters.csv": "fe13a4f336fdc273c808cdfc485b4753",
}


def raw_dir() -> Path:
    return DATA_RAW / "osm_grid" / VERSION


def download() -> Path:
    for name, md5 in FILES.items():
        fetch(
            f"https://zenodo.org/api/records/{RECORD}/files/{name}/content",
            raw_dir() / name,
            md5=md5,
            source_note="vault/data/OSM PyPSA-Eur Grid.md",
            license="ODbL-1.0",
            notes=f"PyPSA-Eur prebuilt OSM network v{VERSION}, Zenodo record {RECORD}",
        )
    return raw_dir()


if __name__ == "__main__":
    print(download())
