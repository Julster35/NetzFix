---
type: data-source
date: 2026-11-03
tags: [data, network, osm, pypsa-eur]
ai-first: true
status: "not accessed yet (2026-11-03)"
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

## Note
- Brief calls this layer "OSM / PyPSA-Eur Grid"; the file name drops the slash for Windows.
