---
type: data-source
date: 2026-11-03
tags: [data, inventory]
ai-first: true
status: "playground v0 inputs downloaded 2026-11-03; all rows in data/MANIFEST.csv"
---

# Raw Data Inventory

## For future agent
What has been downloaded into `data/raw/` (git-ignored), by which code, and its state. Every file has a row in `data/MANIFEST.csv` (url, access date, sha256). `uv run netzfix build` re-creates everything; downloads are cached and skipped if present.

| Source | Code | Output | Coverage | Status (2026-11-03) |
|---|---|---|---|---|
| OSM grid v0.7 ([[OSM PyPSA-Eur Grid]]) | `netzfix.data.osm_grid` | `data/raw/osm_grid/0.7/*.csv` (5 files, md5-checked) | Europe; DE subset used | ✅ |
| MaStR bulk export ([[Marktstammdatenregister]]) | `netzfix.data.mastr` | `data/raw/mastr/data/xml_download/Gesamtdatenexport_20261103.zip` (3.27 GB) → `data/processed/mastr_units_20261103.parquet` (9,716,028 units, 103 XML files, 0 parse errors) | all generation + storage units | ✅ |
| powerplantmatching v0.9.1 | `netzfix.data.ppm` | `data/raw/ppm/powerplants_v0.9.1.csv` | plant coordinates matched to MaStR numbers | ✅ |
| SMARD 2024 ([[SMARD]]) | `netzfix.data.smard` | `data/raw/smard/*.json` (weekly chunks) → `data/processed/smard_DE_2024.parquet` (8,784 h × 15 series, no gaps except nuclear = closed) | DE, hourly 2024 | ✅ |
| Eurostat population NUTS3 | `netzfix.data.regions` | `data/raw/eurostat/demo_r_pjanaggr3_DE_2024.json` | 400 regions, 83.46 M (1 Jan 2024) | ✅ |
| GISCO NUTS 2024 L3 | `netzfix.data.regions` | `data/raw/gisco/NUTS3_2024.geojson` | boundaries | ✅ |
| GISCO LAU 2024 | `netzfix.data.regions` | `data/raw/gisco/LAU_2024.geojson` → `data/processed/lau_DE_2024_points.parquet` | 10,978 DE municipalities with POP_2024 | ✅ |
| ENTSO-E, ERA5, BZR | – | – | – | not downloaded (token / CDS key / Milestone 3) |
