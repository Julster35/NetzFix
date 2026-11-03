# web/ - NetzFix web twin

Static site (Vite + TypeScript + MapLibre GL JS + deck.gl, dark theme, OSM/CARTO base map with attribution). Reads only precomputed artifacts in `web/public/data/` written by `src/netzfix/viz/export_web.py`; no backend. Shows real model output only (a dev fixture must be labelled on screen). Nothing built yet (Milestone 0); first map in Milestone 1. OSM-derived network GeoJSON is ODbL: attribution and share-alike apply.
