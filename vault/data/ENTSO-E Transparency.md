---
type: data-source
date: 2026-11-03
tags: [data, entsoe, load, generation, prices, flows]
ai-first: true
status: "not accessed yet (2026-11-03)"
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
