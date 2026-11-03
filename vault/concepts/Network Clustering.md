---
type: concept
date: 2026-11-03
tags: [clustering, spatial-resolution]
ai-first: true
---

# Network Clustering

## For future agent
The OSM transmission network has thousands of buses; NetzFix aggregates them to N cluster buses (30 for smoke tests, 50-200+ for research) with PyPSA-Eur's clustering. Clustering hides intra-cluster congestion, so results (nodal price spread, redispatch volume, A-vs-C gap) depend on N, which is why cluster size is a sensitivity.

## In PyPSA-Eur v2026.09.0 (config read 2026-11-03)
- `clustering.cluster_network.n_clusters` (default 50), `algorithm: kmeans` (alternative features for `hac`: `wnd100m`, `influx_direct`), `clustering.mode: busmap` (alternative `administrative`), `copperplate_regions`. `stated`
- Lines between clusters are aggregated into equivalent lines. `high`

## Rules for NetzFix
- Clusters must not straddle a bidding-zone border of DE2 or DE5 (U5 in [[Open Questions]]), otherwise B cannot be represented.
- Expectation: more buses -> more visible congestion -> larger redispatch and larger A-vs-C gap. `speculation` (to test as a sensitivity)
- [[Knoerr Bichler Dobos 2025]] use an unclustered 1,670-node DE grid (p. 37). `stated`
