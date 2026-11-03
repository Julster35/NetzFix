---
type: synthesis
date: 2026-11-03
tags: [literature, synthesis]
ai-first: true
status: "Thin (2026-11-03): one benchmark read in depth, seven held items read at abstract/summary level."
---

# Literature Synthesis

## For future agent
What the PDFs we hold actually say about the cost of uniform vs zonal vs nodal pricing in Germany, as of 2026-11-03. One study ([[Knoerr Bichler Dobos 2025]]) quantifies all three designs on one data set; ENTSO-E's BZR report quantifies zonal splits only; EWI argues a firm welfare verdict is not yet possible. Update this note whenever a held PDF is read further.

---

## 1. Size of the gains
- **Zonal splits are small.** [[Knoerr Bichler Dobos 2025]]: 2-4 zones cut total daily cost by 0.44-0.67% vs national (our recomputation from Table 2, p. 19). [[ENTSO-E 2025 BZR Report]]: DE-LU splits gain 251-339 M EUR/yr, DE5 best (p. 8); Knörr et al. report this as < 1% of simulated CE system costs (p. 4). `stated`
- **Nodal is larger.** Knörr et al.: nodal 5.19-5.90% cheaper than any zonal configuration (Table 3, p. 19); the text once says 7-8% (p. 7), inconsistent with the tables. `stated`
- **No firm verdict on welfare.** [[EWI 2025 Policy Brief Gebotszonensplit]]: a conclusive quantitative assessment of a split's welfare effects is not possible yet (p. 5). `stated`

## 2. Why the gap to nodal is large in Knörr et al. (and what that means for us)
- Their redispatch assumes all generators can be redispatched (p. 19), uses MILP unit commitment (p. 18) and fixed costs from Kost et al. (p. 40). With all units redispatchable, the residual gap must come from UC rigidities, curtailment costs and the solver's 5% MIP gap (p. 18). `medium` (our reading; not stated by them in these words)
- For NetzFix's linear model the gap comes only from redispatch frictions ([[Research Design#Why A and C differ at all]]). So our A-vs-C number and theirs measure partly different things; this must be explained in [[Validation]] V7.

## 3. Data
- No public hourly nodal demand for Germany: BZR data publish demand only country-wide (Knörr et al. p. 36). Our demand layer (A12) is a modelling choice either way. `stated`
- The OSM grid used by PyPSA-Eur is ODbL-licensed ([[Xiong et al 2025]] p. 1). `stated`

## 4. Gaps
- No held study on 2024 actual data with open data and open code comparing A/B/C - that is NetzFix's contribution (to confirm after a proper literature search; [[Reading List]]).
