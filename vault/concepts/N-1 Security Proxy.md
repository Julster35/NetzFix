---
type: concept
date: 2026-11-03
tags: [n-1, line-rating, assumption]
ai-first: true
---

# N-1 Security Proxy

## For future agent
Real grids are operated so that any single line can fail without overloading others (n-1). NetzFix does not model contingencies; instead every line may only be loaded to a fraction `s_max_pu` of its thermal rating. Default 0.7, sensitivities 0.6 and 0.8 ([[Assumptions]] A6).

## Notes
- 0.7 is the PyPSA-Eur default `lines.s_max_pu` at v2026.09.0 (read from `config/config.default.yaml`, 2026-11-03) and the value in the PyPSA redispatch example ([[Prior Art]]). `stated`
- It is a blunt proxy: real n-1 margins differ by line, and dynamic line rating and curative measures raise usable capacity. The direction of bias on H1 is unclear, so the sensitivity range matters. `medium`
- [[Knoerr Bichler Dobos 2025]] report line-limit margins of their own (80% in zonal clearing, 20% margin in nodal, per a fetch agent summary of Sec. 1.6 / 2.1.2). Recheck in the PDF before citing. `medium`
