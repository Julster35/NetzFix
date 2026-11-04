---
type: literature
date: 2026-11-04
tags: [literature, grey, bnetza, storage, battery, eeg, mispel]
ai-first: true
pdf: "[[BNetzA_2026-10-01_MiSpeL-Festlegung_Tenor_mit_Begruendung.pdf]]"
citation: "Bundesnetzagentur (2026-10-01). Festlegung zur Marktintegration von Speichern und Ladepunkten (MiSpeL), Az. 618-25-02. Tenor mit Begründung; Hintergrundpapier."
source_url: https://www.bundesnetzagentur.de/DE/Fachthemen/ElektrizitaetundGas/ErneuerbareEnergien/EEG_Aufsicht/MiSpeL/artikel.html
read: "2026-11-04: Hintergrundpapier (4 pp., held as BNetzA_2026-10-01_MiSpeL_Hintergrundpapier.pdf) fully; Tenor mit Begründung (94 pp.) only searched for 'rein netzgekoppelt' (Sonderfall A10/A11) - not read in full"
---

# BNetzA 2026 MiSpeL-Festlegung

## For future agent
BNetzA ruling of 2026-10-01 that lets batteries (and bidirectional charge points) **mix grid power and own solar power** and trade on the market without losing EEG support for the solar share. Before it, a battery behind an EEG-supported PV system could store only green on-site power ("Ausschließlichkeitsoption"), so home batteries ran pure self-consumption. Pure grid-connected batteries without generation were never affected by this EEG conflict (special case A10/A11). Relevant to how NetzFix models batteries: **2024 baseline ≠ post-MiSpeL future**.

## Claims (`stated`, Hintergrundpapier page)
- p. 1: "Bisher: Stromspeicher dürfen ausschließlich grünen Vor-Ort-Strom (z.B. aus einer Solaranlage) speichern, um ihre EEG-Förderung nicht zu verlieren. Ein Mischbetrieb („Multi-Use") führt zum Verlust ihrer EEG-Förderung."
- p. 1: with MiSpeL storage can do market-price and self-consumption optimisation at the same time; cheap power from the roof **or the grid** can be stored and fed back. These rules apply to **direct marketing**, not to fixed feed-in tariff users.
- p. 1-2: **Abgrenzungsoption** (separate meter, 15-min accounting) for all sizes; EEG support kept for stored solar; levy privileges for re-fed grid power, and via legal references also for grid fees. Covers co-located storage (PV park, wind), heat pumps, industry, **pure grid-connected storage** (one-meter case, formula set A11).
- p. 2: **Pauschaloption** for PV ≤ 30 kWp with home storage / bidirectional wallboxes; flat eligibility limit 500 kWh/kWp.
- p. 2: no levy privileges or support for feed-in at **negative prices**.
- p. 3: transition until **2027-09-30**: use needs consent of grid and metering operator; Pauschaloption also awaits state-aid approval.
- Tenor (pp. via search, text lines ~1993-2022): special case "rein netzgekoppelte Stromspeicher ohne sonstige Erzeugung" with a one-meter concept.

## Related law (held)
- Grid-fee exemption for storage: EnWG § 118 Abs. 6 ([[EnWG 13 13a Redispatch]] PDF; paragraph not yet read - to read before use).

## Use in NetzFix (`high` for the logic, `medium` where marked)
- **2024 baseline:** home batteries behind EEG PV (≈ 1.75 million small units, ≈ 10.9 GW in our 2024 assets, computed 2026-11-04) were legally limited to self-consumption → model them as **PV self-consumption** (charge from local PV surplus, discharge into local evening demand), not as market arbitrage. Large stand-alone batteries (50 units ≥ 10 MW, ≈ 1.1 GW) were free to arbitrage; how much they did arbitrage vs balancing reserve in 2024 is not in a held source (`speculation` until sourced).
- **Scenarios after 2027-09:** batteries may arbitrage with grid power (MiSpeL) → market-driven behaviour in the market model (step 3).
- Missing input: usable storage energy (MWh) per unit, needed for any battery rule (MaStR storage tables; to check).
