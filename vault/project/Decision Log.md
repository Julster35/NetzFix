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
