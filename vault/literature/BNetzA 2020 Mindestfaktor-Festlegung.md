---
type: literature
date: 2026-11-04
tags: [literature, grey, bnetza, redispatch, mindestfaktor, core]
ai-first: true
pdf: "[[BNetzA_2020-11-30_Mindestfaktor-Festlegung.pdf]]"
citation: "Bundesnetzagentur (2020-11-30). Beschluss Az. PGMF-8116-EnWG § 13j, Festlegung von näheren Bestimmungen im Zusammenhang mit den Mindestfaktoren (Mindestfaktor-Festlegung)."
source_url: https://www.bundesnetzagentur.de/SharedDocs/Downloads/DE/Sachgebiete/Energie/Unternehmen_Institutionen/Konsultationen/Redispatch/FestlegungMindestfaktoren.pdf
read: "2026-11-04: tenor and pp. 1-7, 39-41 of 44"
---

# BNetzA 2020 Mindestfaktor-Festlegung

## For future agent
BNetzA ruling of 2020-11-30 that sets the **renewables minimum factor to 10** (and a CHP factor of 5, later abolished) for Redispatch 2.0 from 2021-10-01, and orders the four TSOs to compute and publish the uniform calculated prices each year (valid from 1 October). It explains that the calculated price makes renewable curtailment ten times as "expensive" in the selection as a conventional reduction, so priority is relative, not absolute. Numbers we use come from [[netztransparenz Kalkulatorische Preise]]; the law is in [[EnWG 13 13a Redispatch]].

## Claims (`stated`, PDF page)
- Tenor 1 (p. 1): EE minimum factor under § 13 Abs. 1a S. 2 EnWG = **10**.
- Tenor 2 (p. 1): CHP minimum factor under § 13 Abs. 1b Nr. 2 EnWG = **5** (CHP rule later removed from the EnWG; see [[netztransparenz Kalkulatorische Preise]]).
- Tenor 3 (pp. 1-2): TSOs with control-area responsibility determine the calculated EE, CHP and grid-reserve (NR) prices **annually**, valid from **1 October**, publish them by 1 September on a joint website, and publish the **average costs of positive and negative redispatch with non-priority electricity** used in the calculation. In force from 2021-10-01 (tenor 4).
- p. 2-3: reductions of renewables enter the selection of the cheapest measure combination with calculated instead of actual costs; "Je niedriger der EE-Mindestfaktor ist, desto niedriger ist der einheitliche kalkulatorische Preis ... und desto eher werden EE-Anlagen zum negativen Redispatch herangezogen."
- p. 4: the feed-in priority "findet keine absolute Anwendung, sondern wird anhand des Mindestfaktors relativiert"; the ratio must hold "in der Regel", not in every single case. BNetzA may not set separate factors for sub-groups of renewables (one uniform price for all).
- p. 5-6: BNetzA's own simulation used the TSOs' market and grid model (software Integral), nodal for DE and AT, a full year, and an **optimal-power-flow redispatch that minimises cost**, which "entspricht grundsätzlich dem operativen Vorgehen der Übertragungsnetzbetreiber". Minimum factors were converted to prices with the formula on p. 80 of the BMWi study of 2018-04-27 (not held, see [[Reading List#Not held - do not cite]]).
- p. 40: annual (not quarterly) calculation is sufficient; BNetzA found no seasonal pattern in average conventional redispatch costs.
- p. 41: the calculated prices **do not affect the compensation** actually paid for redispatch measures (with BT-Drs. 19/7375 p. 53).

## Use in NetzFix
- Justifies modelling redispatch as a **cost-minimising OPF** with calculated prices for renewables (`stated`, p. 6) - the regulator itself simulates it that way.
- The price formula is not held, but we reconstructed it from the published numbers: see [[netztransparenz Kalkulatorische Preise]] (`high`, computed).
