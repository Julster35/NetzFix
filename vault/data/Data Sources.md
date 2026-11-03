---
type: data-source
date: 2026-11-03
tags: [data, sources, master]
ai-first: true
status: "master list; nothing downloaded yet (2026-11-03)"
---

# Data Sources

## For future agent
Master list of every NetzFix data source, the layer it feeds, its access status and its note. Every download goes to `data/raw/` and gets a row in `data/MANIFEST.csv` (url, access date, sha256); processed tables go to `data/processed/`. Never fabricate data: if a source is down or behind a login, stop and tell Julien.

| Layer | Source | Note | Access | Status (2026-11-03) |
|---|---|---|---|---|
| 1 Grid | PyPSA-Eur OSM network | [[OSM PyPSA-Eur Grid]] | open (ODbL) | not downloaded |
| 2 Units | Marktstammdatenregister | [[Marktstammdatenregister]] | open | not downloaded |
| 3 Wind/PV | ERA5 via atlite | [[ERA5 and atlite]] | **CDS login (U1)** | blocked on login |
| 4 Conventional calibration | ENTSO-E generation per unit | [[ENTSO-E Transparency]] | **API token (U2)** | blocked on token |
| 4 Fuel/CO2 prices 2024 | to choose (A14) | - | - | not chosen |
| 5 Demand | ENTSO-E load + NUTS3 shares | [[ENTSO-E Transparency]], [[DemandRegio]] | token; DemandRegio to check (U4) | not downloaded |
| 6 Cross-border | ENTSO-E flows | [[ENTSO-E Transparency]] | token | not downloaded |
| 7 Validation | SMARD, ENTSO-E prices, netztransparenz, BNetzA | [[SMARD]], [[netztransparenz Redispatch]] | open | not downloaded |
| X Cross-validation | ENTSO-E BZR data | [[BZR dataset]] | open | public, not downloaded |
| X Line ratings / FB | JAO | [[JAO]] | open | optional |

Inventory of what is actually on disk: [[Raw Data Inventory]].
