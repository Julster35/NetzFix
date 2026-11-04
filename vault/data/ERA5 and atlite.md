---
type: data-source
date: 2026-11-03
updated: 2026-11-04
tags: [data, era5, atlite, weather, profiles]
ai-first: true
status: "CDS access works (2026-11-04); 2024 cutout downloading on the chair server (Slurm job 5733)"
---

# ERA5 and atlite

## For future agent
Wind and PV hourly capacity factors per bus for weather year 2024 are computed with atlite (MIT, v0.7.0) from ERA5 reanalysis (Copernicus CDS), then weighted by [[Marktstammdatenregister]] capacity. Layer 3; replaces the single national profile of A20 ([[Assumptions]]) and is the candidate fix for validation test T3 (Q4 share, [[Validation]]). Access works since 2026-11-04; the cutout box is derived from data (A24).

## Use
- atlite cutout for **Germany only** (land + offshore wind farms), 2024 → wind (onshore, offshore) and PV `p_max_pu` per bus, capacity-weighted with [[Marktstammdatenregister]]. Neighbours stay on measured border flows ([[Energy-Charts]]), so they need no weather (A24). `high`
- Also profiles for the hypothetical units in [[Market Value of a Unit]].

## Cutout (A24, set 2026-11-04)
- Code: `src/netzfix/data/era5.py` (`python -m netzfix.data.era5`), Slurm job `jobs/era5.sh`. Config: `weather:` in `config/default.yaml`.
- Box = union of German NUTS3 shapes (GISCO 2024; 5.867-15.041 °E, 47.270-55.057 °N) and MaStR offshore wind units (5.744-14.180 °E, 53.682-55.294 °N), padded by 0.25° and snapped outward to the 0.25° ERA5 grid → **x 5.25-15.5 °E, y 47.0-55.75 °N** (computed 2026-11-04 from `mastr_units_20261103.parquet`). `high`
- Features: `wind`, `influx`, `temperature`; NetCDF, monthly requests. Output: `data/raw/era5/DE_2024_era5.nc` + a MANIFEST row.
- Limitation: the box covers the 2024 offshore fleet only; future farms further out in the North Sea EEZ would need a larger box. `high`

## Access
- Copernicus CDS API, dataset `reanalysis-era5-single-levels`: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels. Account + key by Julien on 2026-11-04; key in `~/.cdsapirc` on the laptop and on the server (never in the repo). The dataset licence must be accepted on the dataset page (a valid key without it gives HTTP 403 "required licences not accepted", observed 2026-11-04); Julien accepted it on 2026-11-04. Licence wording: to record from the dataset page.
- Test request (one hour of 2 m temperature, 2024-01-01 12:00) succeeded on 2026-11-04. The compute node `compute` can reach the CDS (HTTP 200, 2026-11-04).
- https://github.com/PyPSA/atlite (checked 2026-11-03).

## Known issues
- ERA5 wind speeds are known to need bias correction for capacity factors; PyPSA-Eur applies correction factors - document what we use. `medium`
- The first job's MANIFEST row will name `vault/data/ERA5.md` as its note (path fixed in the code after the job started); correct it to this note when the row is merged into the laptop's `data/MANIFEST.csv`.
