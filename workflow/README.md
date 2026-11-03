# workflow/ - PyPSA-Eur integration

NetzFix uses PyPSA-Eur **v2026.09.0** (pinned; see `vault/project/Prior Art.md`) to build and cluster the OSM transmission network for DE + neighbours. Nothing is built here yet (Milestone 0).

Planned (Milestone 1):
- `config.netzfix.yaml` - override of PyPSA-Eur's `config/config.default.yaml`: `countries`, `snapshots`, `clustering.cluster_network.n_clusters`, pinned `data.osm.version`, electricity only.
- `scripts/setup_pypsa_eur.py` (repo root `scripts/`) clones `https://github.com/PyPSA/pypsa-eur` at tag `v2026.09.0` into `workflow/pypsa-eur/` (git-ignored) and copies the override in.
- Run with pixi inside `workflow/pypsa-eur/` up to `clustered.nc`; NetzFix reads that file. WSL2 fallback per the Decision Log.
