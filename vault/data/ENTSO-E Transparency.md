---
type: data-source
date: 2026-11-03
tags: [data, entsoe, load, generation, prices, flows]
ai-first: true
status: "2024 per-unit generation (16.1.A) and internal redispatch (13.1.A) held via File Library (2026-11-04); API token not needed for bulk files"
updated: 2026-11-04
---

# ENTSO-E Transparency

## For future agent
The ENTSO-E Transparency Platform supplies NetzFix's hourly 2024 DE-LU load, actual generation per type and per unit (> 100 MW), cross-border physical flows and day-ahead prices. Access is via the REST API with a personal token, called through `entsoe-py` (MIT, V0.8.1). Layers 4, 5, 6 and validation V1-V3.

## Use
| Item | Use | Layer |
|---|---|---|
| Actual total load DE-LU, hourly 2024 | demand to regionalise ([[Assumptions]] A12) | 5 |
| Actual generation per production type | [[Validation]] V2 | 7 |
| Actual generation per generation unit (> 100 MW) | calibration, V3 | 4 |
| Cross-border physical flows per border | fixed exchange (A13) | 6 |
| Day-ahead prices DE-LU and neighbours | V1 | 7 |

## Access
- Portal: https://transparency.entsoe.eu ; library: https://github.com/EnergieID/entsoe-py (checked 2026-11-03).
- Needs `ENTSOE_API_TOKEN` in `.env` (a personal account: Julien's login, U2 in [[Open Questions]]). Registration steps to verify live when Julien requests it.
- Licence / reuse terms: to read and record at first download.
- Every download -> `data/raw/entsoe/...` + a row in `data/MANIFEST.csv` (url, access date, sha256).

## File Library (no API token) - accessed 2026-11-04
- Logged-in users (free account; Julien's account is his **uni-wuerzburg.de** address) get bulk monthly CSV exports under *My account → File Library → TP_export/<dataset>/YYYY_MM_<dataset>.csv*, each downloadable as ZIP. One export at a time. Terms, privacy and cookie policy accepted by Julien's instruction on 2026-11-04. `stated` (seen in the platform UI).
- Held (MANIFEST rows 2026-11-04, `data/raw/entsoe/`): `ActualGenerationOutputPerGenerationUnit_16.1.A_r3` 2024-01..12 (ZIPs 8.6-10.8 MB; CSV 223-292 MB each, all of Europe, tab-separated) and `RedispatchingInternal_13.1.A_r3.2` 2024-01..12 (42-81 KB ZIPs).
- **16.1.A, Germany 2024** (computed 2026-11-04, `high`): each unit appears once per control area and again under DE_LU / DE_AT_LU; deduplicated by unit + timestamp (control-area rows only) → **176 units**. TWh vs SMARD 2024: lignite 70.05 / 71.0 (29 units, ~99%), hard coal 22.19 / 27.3 (35 units, ~81%), gas 35.48 / 56.9 (58 units, ~62%; plus coal-derived gas 3.92), pumped storage 8.33 / 10.4 (38 units). Hourly and 15-min rows mixed. Columns include unit EIC code, name, type and control area (TSO), not coordinates → match to MaStR needed.
- **13.1.A internal redispatch, Germany 2024** (`high`): 40,258 rows, 7,598 measures; by TSO area: TenneT 20,417, 50Hertz 9,192, Amprion 7,887, TransnetBW 2,762 rows; ActionType/Direction: Load-Decrease 27,139, Generation-Increase 12,276, Generation-Decrease 843; Reason mostly "Load flow overload" (36,175). **No asset names or codes** (all empty): the dataset gives volumes per TSO and time, not per plant. Semantics of "Load Decrease" to check before use.
- Other folders seen: Countertrading_13.1.B, CostsOfCongestionManagement_13.1.C, RedispatchingCrossBorder_13.1.A, ProductionAndGenerationUnits, InstalledGenerationCapacityPerProductionUnit_14.1.B, PhysicalFlows_12.1.G, EnergyPrices_12.1.D, AggregatedGenerationPerType_16.1.B_C.
