---
type: decision-log
date: 2026-11-03
tags: [decisions, core]
ai-first: true
---

# Decision Log

## For future agent
This is the record of design decisions for NetzFix, newest first, each with who decided, the reason and its consequences. If a note elsewhere contradicts this log, the log wins. Open (undecided) items live in [[Open Questions]]. Entries marked "proposed (Claude)" are not decisions until Julien confirms them here.

---

## 2026-11-05 - Web twin is research-only; JAO grid data allowed (Julien)
**Decision:** Julien (2026-11-05): "ok we wont publish the twin and only use it for our reserach". The web twin and model files stay internal; JAO Core Static Grid Model data ([[JAO Core Static Grid Model]]) may be used in the model under JAO's research-use terms (source named).
**Why:** JAO terms allow "educational, academic or research purposes" but restrict redistribution of derived content; the JAO line ratings are the only held per-circuit TSO ratings for all four German TSOs.
**Consequences:** v9 network fix may use JAO Imax. Any later publication (paper figures, a public twin) needs a check against JAO's terms (contact@jao.eu) for what counts as derived content.

---

## 2026-11-05 - Calibration v8 is the model default (Julien)
**Decision:** Julien (2026-11-05): "yes v8 as default". Defaults: `redispatch.rule` cost_based (A25), minimum load (A31), grid-reserve units redispatch-only at p_nr (A32, `grid_reserve.enabled: true`), line margin **0.997** ([[Validation]] "Calibration v8: RESULT"). Supersedes the proposed v7 default (0.991).
**Why:** A32 follows § 13 Abs. 1c EnWG ([[EnWG 13 13a Redispatch]]); tests equivalent to v7 (T1, T4, T5 pass; T2, T3 fail), upward gas closer to 2024.
**Consequences:** the web twin's redispatch now uses the same call as `scripts/calibrate_margin.py` (cost rule, minimum load, reserve; `src/netzfix/server/state.py`) and offers 0.997 as the calibrated limit; before this it ran the v0-v2 minimum-volume rule at 0.933. T1 and T5 pass near the lower edge of their bands. T2/T3 remain documented failures: do not quote offshore-vs-onshore or seasonal redispatch results yet.

---

## 2026-11-03 - Neighbours as Kron-reduced equivalents with measured flows (Julien asked, Claude designed)
**Decision:** Julien: "can we roughly model these outside connections without modeling the whole country? again can we leverage old data here?" Each AC neighbour is reduced from its own OSM grid (already downloaded) to its border substations + a hub; the hourly 2024 physical flow per country from the Energy-Charts API (public, CC BY 4.0) is injected at the hub. Replaces v0 (SMARD residual split by line capacity).
**Why:** v0 put the SMARD residual (40.9 TWh) at the borders although the measured net import was 25.1 TWh, and split it by capacity (e.g. CH 26%, NO 2%; measured PL and CZ are export borders). A first v1 with one copper-plate node per country created ~4 GW of fake transit through NL (gross 5.5 GW on NL border lines vs 1.3 GW net, week of 15 Jan 2024); the Kron equivalent cut it to 3.2 GW.
**Consequences:** 818 buses (38 neighbour buses), 60 equivalent lines; the SMARD gap (15.8 TWh) is domestic (A21b). Validation re-run ([[Validation]]).

---

## 2026-11-03 - Own MaStR parser; powerplantmatching for plant locations (Claude)
**Decision:** parse the MaStR bulk export with our own streaming parser (`src/netzfix/data/mastr.py`) instead of open-mastr; take coordinates of large plants from powerplantmatching v0.9.1 (CC-BY-4.0), matched by MaStR unit number. Supersedes "open-mastr only in a standalone script" in the Part 0 entry below.
**Why:** open-mastr 1.0.0 failed on all solar files and on the combustion file of the 2026-11-03 export (list-valued catalogue fields; log in `data/raw/mastr/logs/open_mastr.log`), which would have silently dropped ~6.6 M solar units and all coal/gas units. The public export has no coordinates for most large plants; district-centre placement stacked e.g. Knapsack I/II and Basell Wesseling onto one 220 kV node.
**Consequences:** no AGPL dependency. 73.0 GW placed via powerplantmatching, 1.1 GW still at district centres ([[Playground]]). Next refinement: connection voltage from the BNetzA Kraftwerksliste.

---

## 2026-11-03 - Re-scope: playground first, optimisation second (Julien)
**Decision (Julien, 2026-11-03, after reviewing Milestone 0):** "for now it would be nice to rebuild the current system as is ... nodes for all the producers and consumers ... built in a way that we could add producers and consumers and play around with their behaviour. Build out a simulation based on known distributions ... the optimisation can be the second step, for now we want to build out the playground which i also want to be able to nicely visualize."
- **Architecture (Julien's choice):** one Python simulation engine + a local web UI served by it (`uv run netzfix serve`); scenarios are edits on top of the 2024 baseline, saved as JSON. Static export for sharing later.
- **Granularity (Julien's choice):** MaStR units ≥ 10 MW are individual producers at their substation; smaller units aggregated per substation and technology; consumers = regional demand per substation.
- **Engine v0 (Claude):** no optimisation. Behaviours (national 2024 profile, demand share, constant, replayed pumped storage, daily price-arbitrage rule) + stochastic modifiers (AR(1) noise, two-state Markov outages) with user-set parameters labelled as assumptions; balancing keeps 2024 net trade and lets dispatchables absorb edits; DC flows by PTDF.
- **Why:** gives a validated "as is" base and an interactive tool before committing to market-design assumptions (O1 etc.), which stay open.
- **Consequences:** Milestones re-ordered in `RESEARCH_PLAN.md` (playground = new Milestone 1; A/B/C comparison moves later). Hypotheses stay unfrozen; the Analysis Log is not needed for playground runs (they are not comparison results), but any number quoted from the playground still cites script + data + commit.

---

## 2026-11-03 - Data sources without login for the playground (Claude)
**Decision:** use sources that need no account so the playground can be built now: PyPSA-Eur OSM network v0.7 from Zenodo (record 18619025, ODbL; v0.7 is the newest version supported by PyPSA-Eur v2026.09.0's `data/versions.csv`, although v0.8 appeared 2026-11-02), MaStR bulk export of 2026-11-03 filtered to units operating at 2024-12-31, SMARD hourly 2024 series (public chart_data API), Eurostat NUTS3 population 1 Jan 2024 + GISCO NUTS 2024 boundaries.
**Why:** ENTSO-E token and CDS key (U1, U2) are still pending; these sources are official and citable.
**Consequences:** v0 has no regional weather (national capacity factors) and population-only demand regionalisation ([[Assumptions]] A12, A17-A21).

---

## 2026-11-03 - BZR data as cross-validation source (proposed (Claude), Julien to confirm)
**Decision:** the ENTSO-E BZR data are added as a **cross-validation** input, not as the primary network. Use: (1) nodal price pattern vs ours, (2) zone maps DE2 / DE5.
**Why:** the data are public (2022 LMP items; 2025 output ZIP 2.72 GB, HTTP 200, no login, checked 2026-11-03), but DE node coordinates and the generator-to-node mapping are not published ([[Knoerr Bichler Dobos 2025]] p. 36), and the target year is 2025 with 2019 input data, not 2024.
**Consequences:** [[BZR dataset]] note; download in Milestone 3, not 1. `stated` (availability), `high` (reasoning)

---

## 2026-11-03 - Reuse decisions (Part 0) (proposed (Claude) per Julien's brief, Julien to confirm)
**Decision:** see [[Prior Art]] for the live-verified table.
- **Build on** PyPSA-Eur **v2026.09.0** (pinned): OSM network, simplification, clustering. Pin the OSM archive version too (`data.osm.version`, not `latest`).
- **Template:** PyPSA redispatch example, generalised (multi-period, storage, restricted pool, zone maps).
- **Libraries:** PyPSA 1.4.x, linopy, atlite, entsoe-py. **open-mastr (AGPL-3.0)** only in a standalone download script that writes CSV/Parquet; `src/netzfix` does not import it, so NetzFix's own licence stays free to choose (O8).
- **Reference only:** PyPSA-DE (cite borrowed assumptions). **Read only:** eTraGo, eGon-data (AGPL).
- **DE fleet from MaStR, DE load from ENTSO-E 2024**, not PyPSA-Eur's defaults.
**Why:** brief Part 0; versions and licences checked via GitHub API 2026-11-03.
**Consequences:** `workflow/` holds a config override; PyPSA-Eur is cloned at the tag (git-ignored).

---

## 2026-11-03 - Windows first, WSL2 fallback (proposed (Claude))
**Decision:** run PyPSA-Eur natively on Windows with pixi (officially supported: `pixi.toml` platforms include `win-64`); switch to WSL2 Ubuntu (already installed) if Snakemake rules fail on Windows. NetzFix's own code runs natively with uv.
**Why:** brief asks for Windows-safe paths and WSL2 only if painful; pixi win-64 support verified at v2026.09.0.
**Consequences:** first test in Milestone 1; outcome logged here.

---

## 2026-11-03 - Project start (Julien)
**Decision:** NetzFix set up per [[2026-11-03 Julien project brief]]: vault conventions mirrored from the-elo-of-e-aura; pre-registration with OpenTimestamps; base year 2024, weather year 2024.
`stated`
