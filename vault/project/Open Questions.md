---
type: plan
date: 2026-11-03
tags: [open-questions, decisions]
ai-first: true
---

# Open Questions

## For future agent
Decisions Julien must take and unknowns to resolve, as of 2026-11-03, ordered by how much they change the answer. O1-O3 must be closed before [[Hypotheses]] is frozen. Closed items move to the [[Decision Log]].

---

## Decisions for Julien
- **O1 - Redispatch frictions (decides H1).** In a linear model, A = C unless redispatch is restricted ([[Research Design#Why A and C differ at all]]). Proposal: base case = German pool rules (RES curtailed last via minimum factors, storage not in the pool, market storage schedule fixed), linear; calibrate against 2024 redispatch volume ([[Validation]] V4-V5); UC as sensitivity.
- **O2 - Threshold X for "cheaper".** Proposal 0.5% of total system cost, robust in all sensitivities. (Knörr et al.'s zonal gains were < 1%, so a 1% bar would almost pre-decide B vs A.)
- **O3 - North/South definition.** Proposal: the DE2 border from the BZR report.
- **O4 - Zone-map digitisation.** BZR maps are figures; proposal: assign NUTS3 regions to zones by hand from the report maps, store as `config/zones/DE2.csv`, `DE5.csv` with the page reference; check against the BZR output data if it carries zone membership.
- **O5 - Inter-zonal capacity in B.** Proposal: NTC-like sum of cutting-line ratings (optimistic), flow-based zonal PTDF as sensitivity.
- **O6 - H3 "profitable" rule.** At ≥ 1 southern bus, or at the load-weighted median southern bus?
- **O7 - WACC** for annualised CAPEX (e.g. 5% / 7%).
- **O8 - Licence** of NetzFix code (MIT proposed) and data outputs (ODbL share-alike applies to OSM-derived network GeoJSON in the web twin).

## Unknowns to resolve
- **U1 - ERA5 access.** atlite needs the Copernicus CDS API (free account + key, a login) for 2024 weather. Does Julien have a CDS account? Otherwise check whether PyPSA-Eur offers a prebuilt 2024 cutout.
- **U2 - ENTSO-E API token.** Needed for load, generation per unit, flows, prices. Registration on transparency.entsoe.eu (a login).
- **U3 - BNetzA 2024 full-year congestion-management report.** Not found at a guessable URL on 2026-11-03; secondary sources quote ~€2.78 bn preliminary for 2024 (`medium`, not held). Download by hand from bundesnetzagentur.de or SMARD.
- **U4 - DemandRegio / FfE access** for NUTS3 demand shares (A12).
- **U5 - PyPSA-Eur busmap per zone:** can clustering be forced not to cross zone borders?
- **U6 - SuedLink parameters** for the counterfactual sensitivity (capacity, route), from a held TSO/BNetzA source.
