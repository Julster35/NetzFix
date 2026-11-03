---
type: data-source
date: 2026-11-03
tags: [data, offshore, hvdc, mastr, osm, reconstruction]
ai-first: true
status: "reconstructed 2026-11-03 from MaStR connection points + OSM HVDC cables; 7.1 GW of the 2024 offshore fleet mapped to landing substations"
---

# Offshore Connections

## For future agent
Where German offshore wind farms come ashore, reconstructed from data rather than from a hand-made list (Julien's question 2026-11-03: "could we reverse engineer the offshore stuff from the data?"). MaStR's grid connection points name the TSO platform of each farm, and OpenStreetMap maps the HVDC export cables; matching is geographic. Code: `src/netzfix/data/offshore.py`; outputs `data/processed/offshore_*.csv`; used by `src/netzfix/network/assets.py` ([[Assumptions]] A19d).

## Inputs `stated`
- [[Marktstammdatenregister]] export 2026-11-03: offshore units (`WindAnLandOderAufSee` = 889) → `LokationMaStRNummer` → `Lokationen` → `NetzanschlusspunkteMaStRNummern` → table `Netzanschlusspunkte`: `NetzanschlusspunktBezeichnung` (TSO naming, e.g. `L-155-DYSK-SWAL-AC120` for DanTysk on SylWin alpha; `L-155-VEMA-BWBE-AC104` for Veja Mate on BorWin beta) and `Nettoengpassleistung` (connection capacity, kW).
- OSM via Overpass (2026-11-03, ODbL): `way["power"="cable"]["name"~"BorWin|DolWin|HelWin|SylWin"]` with geometry, North Sea box; saved `data/raw/osm_overpass/offshore_hvdc_cables.json` (MANIFEST row). Systems found: BorWin1/2/3/5, DolWin1/2/3/5/6, HelWin1/2, SylWin1. Ways naming several systems (shared corridors) are skipped.

## Method
1. Per cable system: onshore point = cable point closest to a ≥ 380 kV grid bus; offshore end = cable point farthest from it.
2. Platform groups (farms sharing a 4-letter TSO platform code BW../DW../HW../SW..) → system whose offshore end is nearest to the group's capacity-weighted centroid. Farms without a code → nearest cable end within 15 km.
3. Landing bus = nearest ≥ 380 kV bus to the system's onshore point.
4. AC-connected North Sea farms (codes EMDB, INHA, HAMA: Riffgat, Nordergründe, alpha ventus) and Baltic farms (50Hertz, no TSO codes) keep the nearest ≥ 380 kV bus.

## Result (2026-11-03) `stated` from `data/processed/offshore_*.csv`
- Cable onshore points lie 0.14-0.28 km from a 380 kV bus, except BorWin5 (16.2 km; onshore route probably incomplete in OSM).
- Geographic matching agrees with the platform codes (alpha=1, beta=2, ...) for BWBE→BorWin2, BWGA→BorWin3, BWEP→BorWin5, DWAL/DWBE/DWGA→DolWin1/2/3, HWAL/HWBE→HelWin1/2, SWAL→SylWin1. BWAL is matched to BorWin2, but BorWin1 and BorWin2 share platform location and landing bus, so the landing is the same. **DWKA (266 MW) is a tie** between DolWin2 and DolWin6 (offshore ends 0.15 km apart) and was assigned DolWin2 (Dörpen) although the code suggests DolWin6 (Emden).
- 2024 fleet: 7,102.8 MW attached via HVDC route, 2,112.3 MW via nearest 380 kV (from `assets_baseline_2024_report.json`).

## Not modelled
- Export-cable capacity limits (only the landing point), offshore platforms as buses, 50Hertz Baltic connections in detail.
