"""ERA5 weather cutout for Germany (regional wind and solar capacity factors, assumptions A2, A24).

Source: Copernicus Climate Data Store, dataset ``reanalysis-era5-single-levels`` (hourly, 0.25 deg),
retrieved through atlite (``Cutout.prepare``), which calls ``cdsapi`` with the key in
``~/.cdsapirc`` (never in the repo). Licence: as stated on the dataset page (accepted there by
Julien on 2026-11-04; wording recorded in vault/data/ERA5 and atlite.md).

The cutout box is derived from held data, not typed in: the union of the German NUTS3 shapes
(GISCO 2024) and the MaStR offshore wind units, padded by ``weather.margin_deg`` and snapped
outward to the 0.25 deg ERA5 grid.
"""

from __future__ import annotations

import argparse
import math
import time
from pathlib import Path
from typing import Any

import pandas as pd

from netzfix.config import DATA_PROCESSED, DATA_RAW, load_config
from netzfix.data.download import append_manifest

ERA5_GRID_DEG = 0.25  # ERA5 single levels native grid (Copernicus product description)
CDS_URL = "https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels"


def snap_bounds(bounds: tuple[float, float, float, float], margin: float,
                grid: float = ERA5_GRID_DEG) -> tuple[float, float, float, float]:
    """Pad ``(xmin, ymin, xmax, ymax)`` by ``margin`` and snap outward to the grid."""
    xmin, ymin, xmax, ymax = bounds
    return (math.floor((xmin - margin) / grid) * grid, math.floor((ymin - margin) / grid) * grid,
            math.ceil((xmax + margin) / grid) * grid, math.ceil((ymax + margin) / grid) * grid)


def data_bounds(nuts_version: int = 2024) -> tuple[float, float, float, float]:
    """Bounding box of German land (NUTS3) and all MaStR offshore wind units."""
    from shapely.geometry import shape
    from shapely.ops import unary_union

    from netzfix.data.regions import geometries

    land = unary_union([shape(f["geometry"]) for f in geometries(nuts_version).values()]).bounds
    mastr = sorted(DATA_PROCESSED.glob("mastr_units_*.parquet"))[-1]
    m = pd.read_parquet(mastr, columns=["Laengengrad", "Breitengrad", "WindAnLandOderAufSee"])
    off = m[m["WindAnLandOderAufSee"] == "Windenergie auf See"].dropna(
        subset=["Laengengrad", "Breitengrad"])
    if off.empty:
        raise RuntimeError(f"no offshore wind units with coordinates in {mastr.name}")
    return (min(land[0], off["Laengengrad"].min()), min(land[1], off["Breitengrad"].min()),
            max(land[2], off["Laengengrad"].max()), max(land[3], off["Breitengrad"].max()))


def cutout_path(cfg: dict[str, Any]) -> Path:
    year = cfg["run"]["weather_year"]
    return DATA_RAW / "era5" / f"{cfg['geography']['focus_country']}_{year}_era5.nc"


def build_cutout(cfg: dict[str, Any], *, retries: int = 4, backoff: float = 60.0,
                 tmpdir: Path | None = None) -> Path:
    """Download and prepare the ERA5 cutout (idempotent), then add a MANIFEST row."""
    import atlite

    w = cfg["weather"]
    year = cfg["run"]["weather_year"]
    path = cutout_path(cfg)
    xmin, ymin, xmax, ymax = snap_bounds(data_bounds(), w["margin_deg"])
    path.parent.mkdir(parents=True, exist_ok=True)
    print(f"cutout {path.name}: x {xmin}..{xmax}, y {ymin}..{ymax}, year {year}, "
          f"features {w['features']}", flush=True)
    last: Exception | None = None
    for attempt in range(retries):
        try:
            cutout = atlite.Cutout(path, module="era5", x=slice(xmin, xmax),
                                   y=slice(ymin, ymax), time=str(year))
            cutout.prepare(features=w["features"], data_format="netcdf", monthly_requests=True,
                           concurrent_requests=w.get("concurrent_requests", False),
                           tmpdir=tmpdir, show_progress=False)
            break
        except Exception as exc:  # CDS queue/network errors; atlite resumes missing features
            last = exc
            print(f"attempt {attempt + 1}/{retries} failed: {exc}", flush=True)
            time.sleep(backoff * 2**attempt)
    else:
        raise RuntimeError(f"ERA5 cutout failed after {retries} attempts: {last}")
    append_manifest(CDS_URL, path, source_note="vault/data/ERA5 and atlite.md",
                    license="Copernicus (see dataset page)",
                    notes=f"atlite cutout, year {year}, x {xmin}..{xmax}, y {ymin}..{ymax}, "
                          f"features {'+'.join(w['features'])}")
    return path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scenario", default=None)
    ap.add_argument("--tmpdir", type=Path, default=None)
    args = ap.parse_args()
    print(build_cutout(load_config(args.scenario), tmpdir=args.tmpdir))


if __name__ == "__main__":
    main()
