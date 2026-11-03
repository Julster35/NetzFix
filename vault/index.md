---
type: index
date: 2026-11-03
tags: [index, catalog]
ai-first: true
---

# NetzFix - Vault Index

Catalog of every note, grouped by folder. Read this before searching. PDFs: `literature/pdfs/` (8 files as of 2026-11-03). Built by `scripts/build_index.py`.

## Root (1)

- [[00_Home]] - Dashboard: Would Germany's power system be cheaper to run with bidding zones or nodal prices than with one price zone plus redispatch, and would locational prices make generation or storage in the south pay off?

## Project (10)

- [[Analysis Log]] - Every specification that is run gets one entry here, **before** its result is looked at, and whatever the result (including failures and smoke tests).
- [[Assumptions]] - Every modelling assumption, with an ID that `config/default.yaml` refers to, its default, its source and why.
- [[Decision Log]] - This is the record of design decisions for NetzFix, newest first, each with who decided, the reason and its consequences.
- [[Hypotheses]] - These are the three testable predictions from Julien's brief with a **proposed** metric and decision rule.
- [[Next Steps]] - Ordered actions as of 2026-11-03, end of Milestone 0.
- [[Open Questions]] - Decisions Julien must take and unknowns to resolve, as of 2026-11-03, ordered by how much they change the answer.
- [[Prior Art]] - This note records which existing open code and data NetzFix reuses and why, verified live on 2026-11-03 (GitHub API, project docs, ENTSO-E site, arXiv).
- [[Research Design]] - This is the full plan for answering the [[Research Question]], written on 2026-11-03 before any model code or data download.
- [[Research Question]] - NetzFix asks whether Germany's power system would be cheaper to run under bidding zones or nodal prices than under today's single price zone plus redispatch, and whether locational prices would make generation or stor...
- [[Validation]] - The model must reproduce the 2024 German system closely enough before any A/B/C comparison result is reported.

## Concepts (8)

- [[Cost-Based Redispatch Compensation]] - In Germany, units called for redispatch are compensated at cost, not at a market bid: a unit ramped up is paid its costs, a unit ramped down pays back the fuel cost it saved, and curtailed renewables are compensated f...
- [[DC Power Flow]] - The linearised ("DC") power-flow approximation used for all NetzFix network optimisations: flows on AC lines follow from voltage-angle differences, losses and reactive power are ignored, voltages are 1 p.u.
- [[Market Value of a Unit]] - The revenue a small (price-taking) unit would earn from energy prices at a given node, per MWh produced and per MW installed per year.
- [[N-1 Security Proxy]] - Real grids are operated so that any single line can fail without overloading others (n-1).
- [[Network Clustering]] - The OSM transmission network has thousands of buses; NetzFix aggregates them to N cluster buses (30 for smoke tests, 50-200+ for research) with PyPSA-Eur's clustering.
- [[Nodal Pricing (LMP)]] - Design **C**: every network node has its own price, the **locational marginal price (LMP)**, from a single optimisation that includes all line limits.
- [[Uniform Pricing and Redispatch]] - Design **A**: Germany (DE-LU) clears as one bidding zone with one price per hour, ignoring internal grid limits; the transmission operators then fix overloads by **redispatch** (raising units behind a congestion, lowe...
- [[Zonal Pricing and Bidding Zones]] - Design **B**: DE-LU is split into 2-5 bidding zones with one price each; only the grid limits between zones are respected in the market, so intra-zonal congestion still needs redispatch.

## Literature (10)

- [[BNetzA 2024 Netzengpassmanagement Q4 2023]] - BNetzA's quarterly congestion-management report for Q4 2023 with full-year 2023 figures (redispatch volumes, costs, curtailment, grid reserve).
- [[Brown Hoersch Schlachtberger 2018]] - The software paper for PyPSA, the modelling library NetzFix uses for all optimisations.
- [[ENTSO-E 2022 LMP Report]] - ENTSO-E's report on the LMP study that produced the nodal prices and the dataset used by [[Knoerr Bichler Dobos 2025]].
- [[ENTSO-E 2025 BZR Report]] - ENTSO-E's main report of the Bidding Zone Review (target year 2025).
- [[EWI 2025 Policy Brief Gebotszonensplit]] - EWI's literature-based policy brief on splitting the DE-LU bidding zone into two.
- [[Hoersch et al 2018]] - The original PyPSA-Eur paper: an open model dataset of the European transmission system with network, power plants, demand and renewable availability.
- [[Knoerr Bichler Dobos 2025]] - **The benchmark NetzFix must discuss its results against.** On ENTSO-E's Bidding Zone Review data for Germany (target year 2025), zonal splits into 2-4 zones cut total cost by less than 1%, nodal pricing by about 5-6%...
- [[Literature Synthesis]] - What the PDFs we hold actually say about the cost of uniform vs zonal vs nodal pricing in Germany, as of 2026-11-03.
- [[Reading List]] - This is the catalog of all literature for NetzFix.
- [[Xiong et al 2025]] - Describes and validates the OpenStreetMap-based European high-voltage grid (>= 200 kV) that PyPSA-Eur uses as `base_network: osm`; it is NetzFix's network layer.

## Data sources (11)

- [[BZR dataset]] - The ENTSO-E Bidding Zone Review data are publicly downloadable (checked 2026-11-03).
- [[Data Sources]] - Master list of every NetzFix data source, the layer it feeds, its access status and its note.
- [[DemandRegio]] - DemandRegio (FfE / project partners) provides electricity demand by NUTS3 region and sector for Germany.
- [[ENTSO-E Transparency]] - The ENTSO-E Transparency Platform supplies NetzFix's hourly 2024 DE-LU load, actual generation per type and per unit (> 100 MW), cross-border physical flows and day-ahead prices.
- [[ERA5 and atlite]] - Wind and PV hourly capacity factors per cluster bus for weather year 2024 are computed with atlite (MIT, v0.7.0) from ERA5 reanalysis, then weighted by MaStR installed capacity within each cluster.
- [[JAO]] - JAO (Joint Allocation Office) publishes the Core static grid model (lines >= 220 kV with ratings) and flow-based market coupling results.
- [[Marktstammdatenregister]] - The Marktstammdatenregister (MaStR) is the BNetzA's official register of all German generation and storage units with location, capacity and commissioning date.
- [[netztransparenz Redispatch]] - netztransparenz.de is the joint information platform of the four German TSOs; it publishes individual redispatch measures (time, TSO, affected units or areas, direction, volume).
- [[OSM PyPSA-Eur Grid]] - The transmission network (220-750 kV AC lines, HVDC, substations) comes from PyPSA-Eur's OpenStreetMap-based base network ([[Xiong et al 2025]]), built and clustered by PyPSA-Eur v2026.09.0 for DE + neighbours.
- [[Raw Data Inventory]] - This lists what has been downloaded into `data/raw/` (git-ignored), by which script, with which MANIFEST rows, and its state.
- [[SMARD]] - SMARD (smard.de) is the Bundesnetzagentur's electricity market data portal: day-ahead prices, generation, consumption and congestion-management (redispatch) data for Germany.

## Figures (1)

- [[Figures]] - Catalog of every plot in `figures/`, one row per PNG with the script, results file and commit that produced it.

## Inputs (1)

- [[2026-11-03 Julien project brief]] - This is the founding brief for NetzFix, pasted by Julien into the first Claude Code session on 2026-11-03 and frozen here verbatim.
