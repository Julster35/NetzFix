---
type: data-source
date: 2026-11-03
tags: [data, network, osm, pypsa-eur]
ai-first: true
status: "v0.7 downloaded 2026-11-03 (Zenodo 18619025, md5 checked); DE grid built"
---

# OSM PyPSA-Eur Grid

## For future agent
The transmission network (220-750 kV AC lines, HVDC, substations) comes from PyPSA-Eur's OpenStreetMap-based base network ([[Xiong et al 2025]]), built and clustered by PyPSA-Eur v2026.09.0 for DE + neighbours. Layer 1. OSM-derived data are under ODbL, which matters for publishing GeoJSON in the web twin.

## Use
- `base.nc -> simplified.nc -> clustered.nc` from the pinned PyPSA-Eur workflow ([[Prior Art]]); NetzFix reads `clustered.nc` and attaches its own units, load and exchange.

## Access
- Workflow: https://github.com/PyPSA/pypsa-eur (tag v2026.09.0); config `electricity.base_network: osm`, data `osm: {source: archive, version: latest}` -> pin the version at first download.
- Prebuilt network on Zenodo (e.g. record 14144752, per web search 2026-11-03; check which version PyPSA-Eur's `archive` points to). `medium`
- Licence: ODbL 1.0 for the OSM-derived dataset (web search 2026-11-03, to verify in [[Xiong et al 2025]]). `medium`

## State (2026-11-03) `stated`
- Version **0.7** (Zenodo record 18619025, 2026-02-12, ODbL), the newest listed as supported in PyPSA-Eur v2026.09.0 `data/versions.csv`; v0.8 (record 23896564) appeared 2026-11-02.
- CSVs quote geometries with `'` (read with `quotechar="'"`). Lines carry `s_nom`, `r`, `x`, `b`, `circuits`; transformers only `s_nom` (x = 0.1 p.u. assumed).
- DE subset: 785 buses (380 kV 450, 220 kV 326, DC 4, other 5); 780 in the largest AC component (5 dropped: 4 HVDC converter buses + 1 stub). 1,019 lines, 153 transformers; 41 cross-border AC lines + 4 HVDC links (NordLink 1,400 MW to NO, Baltic Cable 600 MW to SE, Kontek 600 MW to DK, ALEGrO 1,000 MW to BE) = 45 border points.
- **No offshore wind connection platforms/cables** in this dataset for DE; offshore wind attaches onshore ([[Assumptions]] A19b).

## Note
- Brief calls this layer "OSM / PyPSA-Eur Grid"; the file name drops the slash for Windows.
