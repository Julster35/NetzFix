---
type: plan
date: 2026-11-03
tags: [todo, next-steps]
ai-first: true
---

# Next Steps

## For future agent
Ordered actions as of 2026-11-03, end of Milestone 0. Milestone 0 is done and waiting for Julien's review of [[Prior Art]], [[Research Design]] and `RESEARCH_PLAN.md`. Nothing in Milestone 1 starts before that approval.

> [!todo] Resume here (status 2026-11-03)
> - **Waiting for Julien:** review of Prior Art + Research Design + RESEARCH_PLAN; decisions O1-O8 ([[Open Questions]]); confirm the "proposed (Claude)" entries in the [[Decision Log]].
> - **Julien's logins needed for Milestone 1:** ENTSO-E API token (U2) into `.env`; Copernicus CDS key for ERA5 (U1).

1. Julien reviews Milestone 0. [gate]
2. Download BNetzA 2024 congestion-management report by hand into `literature/pdfs/` (U3).
3. **Milestone 1** (after approval): install PyPSA-Eur v2026.09.0 (pixi, Windows), build OSM network DE + neighbours clustered to ~30 DE buses; MaStR, atlite, ENTSO-E load for one week of 2024; toy-network tests for the market engine; designs A and C; export; first map. Analysis Log #1 as smoke test.
4. Read the held PDFs not yet read in full ([[Reading List]]), starting with [[ENTSO-E 2025 BZR Report]] (zone maps) and [[Xiong et al 2025]].
