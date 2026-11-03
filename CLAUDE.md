# NetzFix - repo instructions for Claude

@vault/_CLAUDE.md

The vault manual above governs research conduct (AI-first notes, literature rule, verify-live, pre-registration). This file covers code.

## Layout
- `src/netzfix/{data,network,markets,analysis,viz}` - the package; `config.py` holds paths and `load_config()`
- `config/default.yaml` (+ `config/scenarios/*.yaml`) - every value maps to an assumption ID in `vault/project/Assumptions.md`
- `workflow/` - PyPSA-Eur config overrides; PyPSA-Eur itself is cloned to `workflow/pypsa-eur/` at a pinned tag (git-ignored)
- `data/raw/` (git-ignored) + `data/MANIFEST.csv` (url, access_date, sha256, ...); `data/processed/`
- `results/<run_id>/`, `timestamps/`, `web/` (Vite + TS + MapLibre + deck.gl), `tests/`, `scripts/`, `notebooks/` (exploration only, never the source of a result)

## Commands (Windows, PowerShell or Git Bash)
- Install: `uv sync`
- Tests: `uv run pytest`
- Lint/format: `uv run ruff check .` / `uv run ruff format .`
- PyPSA-Eur: `pixi` inside `workflow/pypsa-eur` (WSL2 fallback, see Decision Log)

## Code conventions
- Python 3.11+, type hints, `pathlib` paths only (no hard-coded `C:\` or `/` separators), UTF-8 file I/O.
- No numbers that look like data in code. Inputs come from `data/` (with a MANIFEST row) or `config/` (with an assumption ID).
- Every downloader: cache in `data/raw/`, retry with exponential backoff, append a MANIFEST row with sha256. If a source fails or needs a login: stop and tell Julien.
- Secrets only in `.env` (`ENTSOE_API_TOKEN`), never committed or logged.
- open-mastr (AGPL) is used only in `scripts/download_mastr.py`; `src/netzfix` must not import it.
- Market-engine changes need a toy-network test with a hand-computed answer (`tests/`).
- Results are written by scripts, cite run ID + commit, and get an Analysis Log entry **before** the result is looked at.
- Web twin shows real model output only; a dev fixture must be labelled on screen.
- Commit only when asked; each milestone ends with tests passing, a smoke run, a commit, vault updates and second-brain propagation.
