---
type: concept
date: 2026-11-03
tags: [market-design, design-B, bidding-zones]
ai-first: true
---

# Zonal Pricing and Bidding Zones

## For future agent
Design **B**: DE-LU is split into 2-5 bidding zones with one price each; only the grid limits between zones are respected in the market, so intra-zonal congestion still needs redispatch. NetzFix uses two maps from the ENTSO-E Bidding Zone Review 2025: **DE2** (config 2) and **DE5** (config 14).

## Zone maps (from [[ENTSO-E 2025 BZR Report]], read 2026-11-03)
- Table 1 (PDF p. 6) lists the DE-LU alternatives assessed in the BZ study per ACER decision 11/2022, ending with DE4 and DE5. `stated`
- Economic efficiency gains vs status quo, 2025 target year (PDF p. 8): DE5 339 M EUR, DE2 264 M EUR, DE3 251 M EUR; "between 251 million and 339 million" for all DE-LU splits, DE5 best. `stated`
- Config IDs (2 = DE2, 12 = DE3, 13 = DE4, 14 = DE5, German fallbacks replacing configs 1, 3, 4) come from the ENTSO-E BZR web page via a fetch agent (2026-11-03); recheck in the PDF. `medium`
- The brief's "2-zone N/S" is implemented as **DE2** so both maps come from one documented source (proposal, [[Open Questions]] O3/O4).
- Digitisation onto NUTS3 / buses: open (O4). Record page and figure for every assignment.

## Modelling choices
- Market stage: one bus per zone; inter-zonal capacity rule open (O5: NTC-like vs flow-based zonal PTDF). `high`
- Clustering must respect zone borders ([[Network Clustering]], U5).
- [[Knoerr Bichler Dobos 2025]] used the earlier ACER configurations (2 zones k-means / spectral, 3, 4), not DE5 (Table 1, p. 18). `stated`
