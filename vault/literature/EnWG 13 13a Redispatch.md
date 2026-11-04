---
type: literature
date: 2026-11-04
tags: [literature, law, enwg, redispatch, core]
ai-first: true
pdf: "[[EnWG_Stand_2026-11-04_gesetze-im-internet.pdf]]"
citation: "Energiewirtschaftsgesetz (EnWG) vom 7. Juli 2005, zuletzt geändert durch Art. 8 Abs. 6 G v. 23.7.2026 I Nr. 226. gesetze-im-internet.de."
source_url: https://www.gesetze-im-internet.de/enwg_2005/EnWG.pdf
read: "2026-11-04: § 13 Abs. 1-3 (PDF pp. 59-60), § 13a (pp. 62-63), § 13j Abs. 5-6 (pp. 74-75)"
---

# EnWG § 13 / § 13a - the legal redispatch rule

## For future agent
The German Energy Industry Act (EnWG) sets how transmission system operators (TSOs) choose redispatch measures: from the suitable market measures they must pick the combination with the **lowest expected total cost** (§ 13 Abs. 1 S. 2), but curtailing renewables is priced with a uniform **calculated (imputed) price** built from a **minimum factor** of 5-15, so renewables are curtailed only when that replaces a multiple of conventional reduction (§ 13 Abs. 1a). Grid-reserve plants get their own imputed price that makes them come after market plants (§ 13 Abs. 1c). § 13a says who must take part (≥ 100 kW) and how they are compensated (no better, no worse off). This is the rule [[Validation]] calibration v3 implements; see also [[BNetzA 2020 Mindestfaktor-Festlegung]] and [[netztransparenz Kalkulatorische Preise]].

**Version caveat:** the held PDF is the text as of 2026-07-23 (last change Art. 8 Abs. 6 G v. 23.7.2026), not the text in force in 2024. For our 2024 model the relevant content (Abs. 1, 1a, 1c; Abs. 1b on CHP removed) agrees with what the TSOs applied in 2023/24 and 2024/25 (EE and grid-reserve prices only, CHP price "not applicable", [[netztransparenz Kalkulatorische Preise]]). `medium` that no other 2024-relevant wording differed.

## Claims (`stated`, PDF page)
- **§ 13 Abs. 1 S. 1 (p. 59):** if system security in the control area is endangered, TSOs must remove the danger by (1) grid-related measures, especially switching; (2) market-related measures, especially balancing energy, measures under § 13a Abs. 1 (= redispatch), contracted interruptible/switchable loads, congestion information and management; (3) additional reserves, especially the grid reserve (§ 13d) and capacity reserve (§ 13e).
- **§ 13 Abs. 1 S. 2 (p. 59):** for current- and voltage-related adjustments of active-power generation or consumption, among several suitable measures under no. 2 and 3, "die Maßnahmen auszuwählen, die voraussichtlich insgesamt die geringsten Kosten verursachen".
- **§ 13 Abs. 1 S. 3 (p. 59):** plants < 100 kW that a grid operator can remote-control at any time may be used by TSOs **last, regardless of cost** ("unabhängig von den Kosten nachrangig").
- **§ 13 Abs. 1a (pp. 59-60):** to keep the EEG feed-in priority (§ 11 Abs. 1, 3 EEG), reductions of renewable plants (§ 3 Nr. 1 EEG) enter the selection with **calculated costs** from a **uniform calculated price** for all renewable plants. The price must ensure that renewables are reduced only if this "in der Regel ein Vielfaches an Reduzierung von nicht vorrangberechtigter Erzeugung ersetzt" (**Mindestfaktor**). The minimum factor is **at least 5 and at most 15**; BNetzA sets it (§ 13j Abs. 5 Nr. 2).
- **§ 13 Abs. 1b:** "(weggefallen)" (p. 60). (Was the CHP minimum-factor rule; removed - see [[netztransparenz Kalkulatorische Preise]] footnote.)
- **§ 13 Abs. 1c (p. 60):** increases of **grid-reserve** plants (§ 13d) enter with calculated costs from a uniform calculated price; if actual costs are higher, actual costs count. The price must make the reserve "in der Regel nachrangig" to non-priority market plants and must not lead to more renewable curtailment than a selection on actual costs. It is **at least the highest actual price regularly paid** for increasing non-priority, non-reserve plants.
- **§ 13 Abs. 2-3 (p. 60):** if Abs. 1 measures do not suffice, TSOs may adjust all generation, transits and consumption (emergency measures); deviations are allowed where needed, e.g. a technically required minimum feed-in of certain plants ("netztechnisch erforderliches Minimum").
- **§ 13a Abs. 1 (p. 62):** operators of generation or storage plants **≥ 100 kW** (and of smaller remote-controllable ones) must adjust active/reactive power on TSO request; this includes starting plants that are not running and postponing planned revisions.
- **§ 13a Abs. 1a (p. 62):** the balance-responsible party gets a **balancing (energy) compensation** (bilanzieller Ausgleich) from the TSO.
- **§ 13a Abs. 2 (p. 62):** **financial compensation** must leave the operator "wirtschaftlich weder besser noch schlechter" than without the measure. Components: necessary generation expenses, pro-rata wear, proven lost revenue opportunities (if above 1+2), start-up/revision-shift expenses, and for **renewables and CHP electricity: lost income plus extra expenses**. **Saved expenses are paid back** by the operator to the TSO (this is why downward conventional redispatch has negative cost).
- **§ 13a Abs. 4 (p. 63):** standby costs and return on capital are not reimbursed.
- **§ 13j Abs. 6 (p. 75):** BNetzA sets the minimum factor of § 13 Abs. 1a by Festlegung, not below 5 and not above 15.

## What this means for NetzFix (`high`, our reading)
- Redispatch in the model = cost-minimising choice of up/down adjustments subject to line limits, with **conventional plants at (actual) cost**, **renewable curtailment at the calculated EE price**, **grid reserve at the calculated NR price (or actual if higher)**, and **< 100 kW plants only as last resort**. Grid-related measures (switching) come first in law but are not modelled (`speculation` that their effect is partly absorbed by the calibrated line margin, A23).
- Compensation (§ 13a Abs. 2) is a transfer to plant owners; the calculated prices are **selection prices**, not payments (stated in [[BNetzA 2020 Mindestfaktor-Festlegung]] p. 41). Our resource-cost metric ([[Hypotheses]]) must therefore use resource costs, not calculated prices.
