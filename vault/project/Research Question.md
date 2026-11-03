---
type: plan
date: 2026-11-03
tags: [research-question, core]
ai-first: true
status: "Set by Julien's brief 2026-11-03; unchanged."
---

# Research Question

## For future agent
NetzFix asks whether Germany's power system would be cheaper to run under bidding zones or nodal prices than under today's single price zone plus redispatch, and whether locational prices would make generation or storage in the south profitable. The answer must be numerical, open-data, reproducible and pre-registered ([[Hypotheses]]). Source: [[2026-11-03 Julien project brief]].

---

**RQ1 (cost):** Is total system cost lower under (A) one German price zone + redispatch, (B) 2-5 bidding zones + redispatch, or (C) nodal pricing (LMP)? → H1. Metric: [[Hypotheses]]; method: [[Research Design#3. Market designs]].

**RQ2 (prices):** Are southern nodal/zonal prices systematically higher than northern ones? → H2.

**RQ3 (investment signal):** Under nodal/zonal prices, does a PV unit, onshore wind unit, 4h battery or gas peaker become profitable in the south where it is not under the uniform price? → H3; method: [[Market Value of a Unit]].

**Benchmark:** [[Knoerr Bichler Dobos 2025]] find zonal splits save < 1% and nodal 5-6% of total cost on the ENTSO-E BZR data (p. 1; Tables 2-3, p. 19). `stated`. Our results are discussed against theirs.

**Deliverables:** numbers with a falsifiable decision rule; an interactive web twin ([[Research Design#9. Repo structure]], `web/`).
