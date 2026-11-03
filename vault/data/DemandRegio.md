---
type: data-source
date: 2026-11-03
tags: [data, demand, regionalisation, nuts3]
ai-first: true
status: "not accessed yet (2026-11-03)"
---

# DemandRegio

## For future agent
DemandRegio (FfE / project partners) provides electricity demand by NUTS3 region and sector for Germany. NetzFix would use its regional shares to distribute ENTSO-E's hourly national load onto cluster buses (A12); if not accessible, the fallback is population plus industrial employment per NUTS3. Layer 5, the weakest layer.

## Use
- Static NUTS3 shares (households, commerce, industry) x hourly ENTSO-E load -> bus load. Sector-specific profiles if available.

## Access
- To find and verify (U4): the FfE open-data portal / the `disaggregator` package. No URL is recorded until checked live.

## Why it is the weakest layer
- No hourly nodal demand is published in Germany. [[Knoerr Bichler Dobos 2025]] note that the BZR data also only publish country-wide demand (Appendix B, p. 36). `stated`
