---
type: data-source
date: 2026-11-03
tags: [data, jao, static-grid-model, flow-based]
ai-first: true
status: "not accessed yet (2026-11-03)"
---

# JAO

## For future agent
JAO (Joint Allocation Office) publishes the Core static grid model (lines >= 220 kV with ratings) and flow-based market coupling results. NetzFix may use it to cross-check OSM line ratings in Germany and for flow-based inter-zonal capacities in design B (O5).

## Use (optional)
- Line ratings cross-check for DE lines in [[OSM PyPSA-Eur Grid]].
- [[Knoerr Bichler Dobos 2025]] state the JAO Static Grid Model has 837 lines >= 220 kV (footnote 5, p. 4, accessed May 2024). `stated`

## Access
- https://www.jao.eu/static-grid-model (cited by Knörr et al.; check live).
