---
type: concept
date: 2026-11-03
tags: [market-design, design-C, lmp]
ai-first: true
---

# Nodal Pricing (LMP)

## For future agent
Design **C**: every network node has its own price, the **locational marginal price (LMP)**, from a single optimisation that includes all line limits. No redispatch is needed. The LMP is the dual (shadow price) of the node's power balance; price differences between nodes reflect the shadow prices of binding lines.

## Definition
- LOPF: min sum of marginal cost x dispatch s.t. nodal balance, DC flow ([[DC Power Flow]]), line limits |f_l| <= s_max_pu * s_nom ([[N-1 Security Proxy]]), unit limits, storage. `high`
- LMP_n = dual of node n's balance = reference price + sum over lines of (line shadow price x PTDF_{l,n}), sign per PyPSA convention. `high`
- Congestion rent = consumer payments - generator revenues (lossless DC flow) = sum over lines of shadow price x flow. `high`

## In NetzFix
- The benchmark: lowest feasible resource cost given the model ([[Research Design#C - Nodal (benchmark)]]).
- In [[Knoerr Bichler Dobos 2025]], nodal is 5.19-5.90% cheaper than the zonal configurations after redispatch (Table 3, p. 19). `stated`
- Nodal prices in a clustered model are prices of **cluster** buses; their spread is expected to grow with cluster count ([[Network Clustering]]). `medium`
