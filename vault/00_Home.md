---
type: index
date: 2026-11-03
tags: [home, moc]
ai-first: true
---

# NetzFix - Knowledge Graph

> *Would Germany's power system be cheaper to run with bidding zones or nodal prices than with one price zone plus redispatch, and would locational prices make generation or storage in the south pay off?*

An open-data model of the German transmission grid (PyPSA-Eur OSM network, MaStR fleet, atlite weather, ENTSO-E load, base year 2024) runs three market designs on the same system: **A** uniform + redispatch, **B** 2-5 zones + redispatch, **C** nodal. The answer is pre-registered ([[Hypotheses]]) and sealed with OpenTimestamps before any comparison. An interactive web twin shows the results.

**Status (2026-11-04, end of session):** Digital twin of 2024 with the **legal redispatch rule** (§ 13 EnWG cost order, minimum factor 10, TSO calculated prices), **real 2024 output of 178 large thermal units** (ENTSO-E File Library), **regional ERA5 weather** with pre-curtailment wind/solar, **minimum load** of 394 units and a price layer (2024 frozen / latest / user). [[Validation]] v7: line margin 0.991, **T1, T4, T5 pass**; T2 (offshore share) and T3 (Q4 share) fail. v8 (grid-reserve units, A32, 2026-11-05): margin 0.997, same three tests pass. CHP must-run (A33) prepared. Diagnostics: December = 36% of model volume, 220 kV artefact overloads up to 3.1×. See [[Next Steps]]. A/B/C later, hypotheses unfrozen.

---

## Research
- [[Research Question]]: RQ1 cost, RQ2 prices, RQ3 investment signal
- [[Research Design]]: pipeline, designs A/B/C, metric, validation, sensitivities ⭐
- [[Hypotheses]]: H1-H3, draft, **not frozen**
- [[Assumptions]]: A1-A16, mirrors `config/default.yaml`
- [[Validation]]: the gate before any comparison
- [[Prior Art]]: what we reuse (verified 2026-11-03)
- [[Playground]]: the 2024 grid as is, assets, behaviours, UI ⭐

## Concepts
- [[Uniform Pricing and Redispatch]] · [[Zonal Pricing and Bidding Zones]] · [[Nodal Pricing (LMP)]]
- [[Cost-Based Redispatch Compensation]] · [[Market Value of a Unit]]
- [[DC Power Flow]] · [[N-1 Security Proxy]] · [[Network Clustering]]

## Literature (PDFs in `literature/pdfs/`)
- [[Literature Synthesis]] ⭐ · [[Reading List]]
- Benchmark: [[Knoerr Bichler Dobos 2025]] · [[ENTSO-E 2025 BZR Report]]

## Data
- [[Data Sources]] (master) · [[Raw Data Inventory]] · [[BZR dataset]]

## Project
- [[Decision Log]] · [[Analysis Log]] · [[Next Steps]] · [[Open Questions]]
- Founding brief: [[2026-11-03 Julien project brief]]

---

## The One-Paragraph Summary (as of 2026-11-03)
The only held study that compares all three designs on one German data set, [[Knoerr Bichler Dobos 2025]], finds that splitting DE-LU into 2-4 zones cuts total cost by less than 1%, while nodal pricing cuts it by 5-6% (Tables 2-3, p. 19), on ENTSO-E's BZR data for target year 2025. ENTSO-E's own BZR report finds DE-LU splits gain 251-339 M EUR/yr, DE5 best ([[ENTSO-E 2025 BZR Report]] p. 8). NetzFix redoes the comparison on the **actual 2024 system** with open data and open code. One structural fact shapes the whole project: in a linear model, uniform pricing plus fully flexible cost-based redispatch reaches exactly the nodal cost, so the A-vs-C gap measures **redispatch frictions**, which must be grounded in German rules, calibrated to 2024 redispatch data and frozen before the bet is settled.
