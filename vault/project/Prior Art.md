---
type: plan
date: 2026-11-03
tags: [prior-art, reuse, licences, core]
ai-first: true
status: "Part 0 verified live 2026-11-03: build on PyPSA-Eur v2026.09.0 (OSM network, clustering) + PyPSA v1.4 redispatch pattern; MaStR, atlite, entsoe-py as libraries; PyPSA-DE reference only; eTraGo/eGon read-only; BZR data public and added as cross-validation source."
---

# Prior Art

## For future agent
This note records which existing open code and data NetzFix reuses and why, verified live on 2026-11-03 (GitHub API, project docs, ENTSO-E site, arXiv). Rule: only write what does not exist yet. Reuse decisions are mirrored in the [[Decision Log]] (entry 2026-11-03 "Reuse decisions (Part 0)"); if they differ, the log wins.

---

## 1. Code: verified state (GitHub API, queried 2026-11-03 ~12:40 CET)

| Repo | Licence (live) | Last push | Latest release | Use in NetzFix | Conf. |
|---|---|---|---|---|---|
| [PyPSA/pypsa-eur](https://github.com/PyPSA/pypsa-eur) | REUSE multi-licence: `LICENSES/` holds MIT, CC-BY-4.0, CC-BY-SA-4.0, CC0-1.0 (code MIT; docs/data CC). The brief's "MIT" is right for code. | 2026-11-03 | **v2026.09.0** (2026-09-25) | **Build on.** OSM base network, simplify + cluster, (optionally) its cutout/profile rules. Pin v2026.09.0. | stated |
| [PyPSA/PyPSA](https://github.com/PyPSA/PyPSA) | MIT | 2026-11-03 | v1.4.0 (2026-10-09) | Core modelling library | stated |
| [PyPSA/linopy](https://github.com/PyPSA/linopy) | MIT | 2026-11-03 | v0.10.1 (2026-10-21) | Optimisation layer (via PyPSA) | stated |
| [PyPSA/atlite](https://github.com/PyPSA/atlite) | MIT | 2026-10-15 | v0.7.0 (2026-10-07) | Wind/PV capacity factors from ERA5 | stated |
| [PyPSA/powerplantmatching](https://github.com/PyPSA/powerplantmatching) | REUSE: MIT, Apache-2.0, CC-BY-4.0, CC0 | 2026-11-01 | v0.9.1 (2026-10-07) | Neighbour countries' fleets only (DE fleet from MaStR) | stated |
| [PyPSA/pypsa-de](https://github.com/PyPSA/pypsa-de) | REUSE: MIT, CC-BY-4.0, CC-BY-SA-4.0, CC0 | 2026-11-03 | v0.4 (2026-10-05) | **Reference only.** Borrow German assumptions with citation; do not fork (sector-coupled, heavy). | stated |
| [OpenEnergyPlatform/open-MaStR](https://github.com/OpenEnergyPlatform/open-MaStR) | **AGPL-3.0** | 2026-11-02 | v1.0.0 (2026-09-24) | Download MaStR bulk export. Called only from a standalone download script (see licence note below). | stated |
| [EnergieID/entsoe-py](https://github.com/EnergieID/entsoe-py) | MIT | 2026-10-13 | V0.8.1 (2026-09-04) | ENTSO-E load, generation per unit, flows, prices | stated |
| [openego/eTraGo](https://github.com/openego/eTraGo) | AGPL-3.0 | 2026-11-03 | 0.11.0 (2026-08-18) | **Read only** for method comparison | stated |
| [openego/eGon-data](https://github.com/openego/eGon-data) | AGPL-3.0 | 2026-10-30 | v2.0.0 (2025-08-20) | **Read only** | stated |

### PyPSA-Eur specifics (read from `config/config.default.yaml` and `doc/` at tag v2026.09.0, 2026-11-03)
- `electricity.base_network: osm` is the default; the OSM network is retrieved under `data.osm` (`source: archive`, `version: latest`) - we must pin the archive version, not `latest`. `stated`
- `countries:` list, `snapshots: {start, end}`, `lines.s_max_pu: 0.7` default, `clustering.cluster_network.n_clusters` (default 50, `algorithm: kmeans`), `clustering.mode: busmap` or `administrative`, `clustering.copperplate_regions`, `clustering.build_bidding_zones` (sources `bidding_zones_electricitymaps` / `bidding_zones_entsoepy`). `stated`
- **v2026.09.0 restructured the workflow**: `base.nc -> simplified.nc -> clustered.nc -> composed_{horizon}.nc -> solved_{horizon}.nc`; cluster count etc. now set in config, not wildcards ([release notes](https://github.com/PyPSA/pypsa-eur/blob/v2026.09.0/doc/release_notes.md)). Older tutorials with `elec_s_37_...nc` names are outdated. `stated`
- **Windows:** environment managed with **pixi**; `pixi.toml` lists platforms `win-64, linux-64, osx-64, osx-arm64`; conda pin file `envs/default_win-64.pin.txt` exists ([installation.md](https://github.com/PyPSA/pypsa-eur/blob/v2026.09.0/doc/installation.md)). So native Windows is officially supported; WSL2 (Ubuntu already installed on this laptop) is the fallback. `stated`
- Docs moved: `pypsa-eur.readthedocs.io/en/latest/` resolves (200) but the old `installation.html` path 404s (now mkdocs pages). `stated`
- OSM network paper: [[Xiong et al 2025]] (held). `stated`

### PyPSA redispatch example (read 2026-11-03, docs.pypsa.org)
Source: https://docs.pypsa.org/latest/examples/scigrid-redispatch/ (HTTP 200, read via fetch agent 2026-11-03).
- Pattern: (1) nodal benchmark `o.optimize()`; (2) zonal model by mapping buses to zones (`n.buses.y > 51` -> North/South), removing intra-zonal lines, `m.optimize()`; (3) fix nodal generator dispatch to the zonal result via `p_min_pu = p_max_pu = p/p_nom`; (4) add `"ramp up"` copies (`p_max_pu` = headroom) and `"ramp down"` copies (`p_min_pu = -p/p_nom`, `p_max_pu = 0`); (5) re-optimise. Single snapshot, SciGRID-DE, `s_max_pu = 0.7`, storage ignored. `stated`
- **Key fact for H1:** with redispatch costed at unchanged marginal cost, redispatch cost = nodal cost exactly (example: 301 k€ both); only when up-cost is ×2 and down-credit ×0.5 does it diverge (502 k€). → In a pure LP, design A only differs from C in resource cost through **redispatch frictions**. See [[Research Design#Why A and C differ at all]]. `stated` (example), `high` (generalisation)
- What we add: multi-period, storage, real data, configurable zone maps, cost-based compensation per [[Cost-Based Redispatch Compensation]], a restricted redispatch pool.

## 2. Benchmark: Knörr, Bichler, Dobos (arXiv 2403.09265 v6, 2 Jun 2025)
Held: [[Knoerr Bichler Dobos 2025]]. Summary of what matters for us (all `stated`, PDF pages):
- Data: ENTSO-E's 2022 LMP data release of the BZR process (target year 2025, input data collected 2019), German grid 1,670 nodes / 2,407 lines (p. 37); 4,537 units (p. 38); 8 weeks of climate year 2009 (p. 18); MILP unit commitment, Gurobi, 5% MIP gap (p. 18).
- Configurations: National, 2 Zones (k-means), 2 Zones (spectral), 3 Zones, 4 Zones (ACER 2022 alternatives) vs Nodal - **not** the final BZR 2025 DE5 map.
- Table 2 (p. 19) average daily total cost after min-cost redispatch: National 38,285.14 k€, 2Z(k) 38,116.38, 2Z(s) 38,082.91, 3Z 38,026.81, 4Z 38,109.64, Nodal 36,150.7. Table 3: nodal is 5.19-5.90% cheaper. Abstract: zonal savings < 1%, nodal 5-6% (p. 1). The intro says "around 7-8%" (p. 7), inconsistent with Tables 2-3 → we cite Tables 2-3.
- No code release found. Data: "accessible through the ENTSO-E website", but local demand aggregated to national level and no generator-to-node mapping (Appendix B, p. 36).

## 3. Is the BZR dataset publicly downloadable? **Yes** (checked 2026-11-03)
Source: [ENTSO-E BZR page](https://www.entsoe.eu/network_codes/bzr/). Details in [[BZR dataset]].
- **2022 LMP data items** (what Knörr et al. used): `Input_files.zip`, `Nodal_Prices.zip`, `Flows in Network.zip`, `Cleared_Generation.zip`, `Constraints_and_Shadow_Prices.zip`, etc. under `entsoe.eu/documents/nc/NC CACM/BZR/`, no login stated; plus a "Request the dataset" link to `stum.entsoe.eu`. `stated` (page text, via fetch agent)
- **BZR 2025 output data** (published by 28 May 2025): `BZRR_CE_output_data.zip` on the ENTSO-E blob CDN, HTTP 200, **2.72 GB**, no login (HEAD request 2026-11-03). `stated`
- Main report held: [[ENTSO-E 2025 BZR Report]] - DE5 has the highest economic efficiency gain of the DE-LU splits, 339 M€/yr; range 251-339 M€ (PDF p. 8). `stated`
- **Decision:** add as cross-validation source (nodal price pattern, zone maps), not as the primary network: no DE node coordinates published and no generator-node mapping ([[Knoerr Bichler Dobos 2025]] p. 36). See [[Decision Log]].

## 4. Policy context (secondary sources, not held - do not cite as evidence)
- Web search 2026-11-03: the German economics ministry published an "Aktionsplan Gebotszone" on 2025-12-15 keeping the single DE-LU zone ([BMWE press release](https://www.bundeswirtschaftsministerium.de/Redaktion/DE/Pressemitteilungen/2025/12/20251215-erhalt-der-einheitlichen-stromgebotszone.html)). `medium` - fetch and hold before citing.

## 5. What NetzFix writes itself (gap analysis)
1. MaStR → bus mapping of DE units, with capacities as of 2024 (PyPSA-Eur uses powerplantmatching / OPSD for DE). 
2. ENTSO-E 2024 load regionalised to clustered buses ([[Assumptions]] A12).
3. Market-design engine A/B/C, multi-period, storage-aware, with zone maps and a restricted redispatch pool (generalising the PyPSA example).
4. Market value of hypothetical units per node ([[Market Value of a Unit]]).
5. Validation against 2024 prices, mix, redispatch ([[Validation]]).
6. Web exporter + Vite/MapLibre/deck.gl twin.
