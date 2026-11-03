# Claude Operating Manual - NetzFix Research Vault

> Read this file before doing anything in this vault.
> This is the single source of truth for how Claude operates here.
> Navigate with [[index]] first (full catalog), then search.

---

## Section 0 - AI-First Vault Rule (read first, applies to every note)

This vault is designed for **future agent** to read and reason over. The owner (Julien) rarely reads notes directly and calls Claude to retrieve, synthesize, and connect dots across the research record.

**Every NEW note Claude writes to this vault must follow these rules:**

1. **Self-contained context** - Each note must explain itself. Future-Claude may pull this single note via search with no surrounding context.
2. **"For future agent" preamble** - Every new note begins with a `## For future agent` section: a 2-3 sentence plain-English summary so Claude can decide relevance in 10 seconds.
3. **Rich, consistent frontmatter** - `type`, `date`, `tags`, `ai-first: true`, plus `status` for findings and `pdf:` for literature notes.
4. **Recency markers per claim** - "PyPSA-Eur latest release is v2026.09.0 (as of 2026-11-03)".
5. **Sources preserved verbatim** - Web sources with URL inline; results cite the **script + data file + commit** they were computed from.
6. **Cross-links are mandatory** - Every concept, finding, data source or decision referenced uses `[[wikilinks]]`.
7. **Confidence levels** - Mark claims `stated | high | medium | speculation`.
   - `stated`: read verbatim in a held PDF, a live web page, or our own result file (cite it).
   - `high`: textbook power-system / market-design fact, or directly computed by us.
   - `medium`: secondary source, or an inference with one weak step.
   - `speculation`: our guess; must never carry a result.

---

## Section 0.25 - THE LITERATURE RULE (project-specific, non-negotiable)

**We only rely on literature we hold the PDF for.** (Owner instruction, 2026-11-03.)

- Every PDF lives in `literature/pdfs/`. Every literature note has `pdf: "[[file.pdf]]"` in frontmatter.
- A literature note may only state what is in its PDF. Numbers are quoted with **table / page** reference. Page = PDF page unless marked "printed p.".
- Papers we know of but do **not** hold are listed in [[Reading List#Not held - do not cite]]. They may be mentioned as "cited in X" but never used as evidence.
- **Grey literature** (ENTSO-E BZR study, BNetzA reports, EWI briefs, TSO reports) counts as held only once the PDF is downloaded into `literature/pdfs/`.
- When a held PDF is a preprint of a published article, say so (e.g. [[Knoerr Bichler Dobos 2025]] is arXiv v6, journal: Energy Economics) - numbers may differ from the version of record.

---

## Section 0.5 - Verify Live State Before Acting

- Read the actual data (the `.nc` network, the CSV, the API response) before declaring a result.
- Recompute a number before quoting it. Never quote a number from memory or training data.
- Fetch live figures: repo releases, licences, data-portal URLs, prices, published redispatch costs. Note the access date.
- **Never fabricate data.** If a source is unavailable or behind a login: stop and tell Julien. The web twin shows only real model output (a dev fixture must be labelled as such on screen).

---

## Section 1 - Pre-registration and the bet

There is a bet riding on the answer. These rules make the answer defensible:

1. [[Hypotheses]] holds H1-H3, the exact metric, the decision rule and what counts as "cheaper". It is **frozen before any A/B/C comparison run** and sealed with OpenTimestamps (`timestamps/`, see `timestamps/README.md`). The anchor commit goes into the [[Decision Log]].
2. The [[Analysis Log]] gets an entry for **every specification before its result is looked at**, whatever the result. Newest at the bottom. Smoke tests are logged too, labelled "smoke test, not a result".
3. The [[Decision Log]] (newest first: decision, who, reason, consequences) **overrides any other note**.
4. [[Validation]] must pass (or its failures be documented and accepted by Julien in the Decision Log) **before** any comparison result is reported.
5. Report against H1-H3 whatever the result, including in every sensitivity.

---

## Vault Identity

- **Owner:** Julien Froidefond (M.Sc., JMU Würzburg)
- **Project:** NetzFix - an open-data model of the German transmission grid that compares total system cost under (A) one price zone + redispatch, (B) 2-5 bidding zones + redispatch, (C) nodal pricing, and asks whether southern generation/storage becomes profitable under B/C. See [[Research Question]].
- **Repo:** `C:/Users/julie/Documents/NetzFix` (this vault is `vault/`; code in `src/netzfix/`, config in `config/`, PyPSA-Eur overrides in `workflow/`, raw data in `data/raw/` (git-ignored, listed in `data/MANIFEST.csv`), web twin in `web/`, plan in `RESEARCH_PLAN.md`)
- **Founding brief:** [[2026-11-03 Julien project brief]]
- **Style reference vault:** `../the-elo-of-e-aura/vault` (same conventions, different project)
- **Second brain:** `C:/Users/julie/Documents/SecondBrain` - project note `Projects/NetzFix.md`; summaries only, detail stays here.
- **Created:** 2026-11-03

---

## Folder Map

| Folder | Purpose |
|---|---|
| `project/` | Research question, design, hypotheses, assumptions, validation, logs, plans. `status:` in frontmatter is a one-line verdict |
| `concepts/` | Market-design and power-system concepts (uniform/zonal/nodal pricing, DC power flow, n-1 proxy, market value, clustering, redispatch compensation) |
| `literature/` | One note per held paper + [[Reading List]] + [[Literature Synthesis]]. PDFs in `literature/pdfs/` |
| `data/` | [[Data Sources]] (master), one note per source, [[Raw Data Inventory]] |
| `figures/` | Plot PNGs + [[Figures]] note |
| `inputs/` | Frozen external inputs, `YYYY-MM-DD Who what.md` |
| `outbox/` | Notes sent to others, `YYYY-MM-DD Julien to X topic.md` |
| `Logs/` | Per-day vault operations log (see [[log]]) |

---

## Key Files

- **Catalog:** [[index]] - read first, update on every new note
- **Dashboard:** [[00_Home]] - update the dated status line at the end of each milestone
- **The plan:** [[Research Design]] (and `RESEARCH_PLAN.md` at repo root)
- **Reuse decisions:** [[Prior Art]]
- **Pre-registration:** [[Hypotheses]] · [[Analysis Log]] · [[Decision Log]]
- **Open work:** [[Next Steps]], [[Open Questions]]

---

## Conventions

- **Market designs** are always named `A` (uniform + redispatch), `B` (zonal + redispatch, with the zone map named: `B-DE2`, `B-DE5`), `C` (nodal). See [[Uniform Pricing and Redispatch]], [[Zonal Pricing and Bidding Zones]], [[Nodal Pricing (LMP)]].
- **Total system cost** means the resource cost defined in [[Hypotheses]] (not consumer payments). Never mix the two in one number.
- **Units:** €, MW, MWh, TWh; prices €/MWh; market value €/MWh and €/MW/yr; costs per year unless stated. Signs: redispatch "up" = positive MWh, "down" = negative.
- **North / South** of Germany: defined once in [[Assumptions]] (zone map), never ad hoc.
- **Run IDs:** `<design>_<zonemap>_<year>w<weatheryear>_<nbus>b_<res>_<smaxpu>` e.g. `C_nodal_2024w2024_30b_3h_0.7`.
- **Dates** in notes are absolute (YYYY-MM-DD).

---

## End of every working session

1. Logs/ entry for today; [[index]] updated for new notes; [[00_Home]] status line; [[Next Steps]].
2. Commit (tests passing).
3. Second brain: update `SecondBrain/Projects/NetzFix.md`, add `SecondBrain/Dev Logs/YYYY-MM-DD - NetzFix <topic>.md`, add a line to `SecondBrain/Daily/YYYY-MM-DD.md`. Ask before deleting or archiving anything there.
