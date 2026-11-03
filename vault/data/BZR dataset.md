---
type: data-source
date: 2026-11-03
tags: [data, bzr, entsoe, cross-validation, zone-maps]
ai-first: true
status: "public, not downloaded (checked 2026-11-03)"
---

# BZR dataset

## For future agent
The ENTSO-E Bidding Zone Review data are publicly downloadable (checked 2026-11-03). Two parts matter: the 2022 LMP data items (grid model inputs, nodal prices, flows, cleared generation; the set Knörr et al. used) and the BZR 2025 output data (CE region ZIP, 2.72 GB). NetzFix uses them for cross-validation of nodal price patterns and for the DE2 / DE5 zone maps, not as the primary network.

## What is there (from https://www.entsoe.eu/network_codes/bzr/ via fetch agent, plus own HTTP checks, 2026-11-03)
- **2022 LMP data items** (LMP study ran 24 Nov 2020 - 4 Mar 2022): `Input_files.zip`, `Nodal_Prices.zip`, `Flows in Network.zip`, `Cleared Demand.zip`, `Cleared_Generation.zip`, `Cleared_Storage.zip`, `Constraints_and_Shadow_Prices.zip`, `Socio-Economic_Welfare.zip` under `https://www.entsoe.eu/documents/nc/NC%20CACM/BZR/`. A "Request the dataset" link points to https://stum.entsoe.eu (terms not stated). `stated` (page text)
- **BZR 2025 output data**: `https://eepublicdownloads.blob.core.windows.net/public-cdn-container/clean-documents/Network%20codes%20documents/NC%20CACM/BZR/2025/BZRR_CE_output_data.zip` - HTTP 200, Content-Length 2,719,346,917 bytes, no login (HEAD request 2026-11-03). Description PDF: `.../NC%20CACM/BZR/OutputData/BZRR_CE_Output_Data_Description.pdf`. `stated`
- **Annex 2 CE input data** (xlsx) and the main report: [[ENTSO-E 2025 BZR Report]] (held). `stated`
- Note: `www.entsoe.eu/documents/...` refused our curl request (HTTP 000) while the blob CDN served the same report; use the CDN host. `stated`

## Limits
- Target year 2025 with input data collected in 2019; DE grid 1,670 nodes / 2,407 lines after pre-processing in [[Knoerr Bichler Dobos 2025]] (p. 37). `stated`
- Local demand aggregated to country level; generator-to-node mapping not published (Knörr et al. Appendix B, p. 36). `stated`
- DE node coordinates: Knörr et al. "manually determined the geographical locations of all substations" (Appendix B, via fetch agent; recheck in PDF). `medium`

## Plan
- Milestone 3: download the 2025 output ZIP and its description; record in MANIFEST; read the description before using anything ([[Decision Log]] 2026-11-03).
