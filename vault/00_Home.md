---
type: index
date: 2026-11-03
tags: [home, moc]
ai-first: true
---

# NetzFix - Knowledge Graph

> *Would Germany's power system be cheaper to run with bidding zones or nodal prices than with one price zone plus redispatch, and would locational prices make generation or storage in the south pay off?*

An open-data model of the German transmission grid (PyPSA-Eur OSM network, MaStR fleet, atlite weather, ENTSO-E load, base year 2024) runs three market designs on the same system: **A** uniform + redispatch, **B** 2-5 zones + redispatch, **C** nodal. The answer is pre-registered ([[Hypotheses]]) and sealed with OpenTimestamps before any comparison. An interactive web twin shows the results.

**Status (2026-11-05, end of session):** Model default **v8** (legal cost rule, real thermal output, regional weather, min load, grid-reserve units; margin 0.997): **T1, T4, T5 pass**, T2 (offshore share) and T3 (Q4 share) fail. New yardstick **T6** from the TSOs' 2024 redispatch measures (netztransparenz) fails on monthly shape, daily timing and TSO split (TransnetBW 2x too high). **v9** with TSO line ratings ([[JAO Core Static Grid Model]], research use only) needs 34.5 TWh even at 100% rating → no calibrated margin. Next: v10 phase shifters, v11 weather-dependent ratings (needs IEEE 738/CIGRE PDF), v12 CHP must-run. Twin stays internal ([[Decision Log]]). See [[Next Steps]]. A/B/C later, hypotheses unfrozen.

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
