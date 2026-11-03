---
type: plan
date: 2026-11-03
tags: [assumptions, config, core]
ai-first: true
status: "A1-A15 registered 2026-11-03; mirrors config/default.yaml. Demand regionalisation (A12) is the weakest layer."
---

# Assumptions

## For future agent
Every modelling assumption, with an ID that `config/default.yaml` refers to, its default, its source and why. If code and this note disagree, fix one of them in the same commit (`tests/test_config.py` checks the core defaults). Sources marked "to cite" must get a held source or a live URL before the first comparison run.

---

| ID | Assumption | Default | Source / reason | Conf. |
|---|---|---|---|---|
| A1 | Base year (fleet, demand, prices) | 2024 | Brief; latest full year with published redispatch data | stated |
| A2 | Weather year | 2024 | Brief; consistent with A1 | stated |
| A3 | Geography | DE+LU detailed; AT, BE, CH, CZ, DK, FR, NL, NO, PL, SE one bus each | DE-LU is one bidding zone; neighbours of DE-LU | high |
| A4 | Network source | PyPSA-Eur v2026.09.0 `base_network: osm`, OSM archive version pinned at download | [[Prior Art]], [[Xiong et al 2025]] | stated |
| A5 | Spatial resolution | 30 buses (smoke) → 50 / 100 / 200+ | Brief; [[Network Clustering]] | stated |
| A6 | Line rating | `s_max_pu = 0.7` (sens. 0.6 / 0.8) | n-1 proxy; also the PyPSA-Eur default ([[N-1 Security Proxy]]) | stated |
| A7 | Power flow | linear DC, lossless | [[DC Power Flow]] | high |
| A8 | Time resolution | 3 h, one week (smoke) → representative weeks → full hourly 2024 | Brief; runtime | stated |
| A9 | Zone maps | DE2 = BZR config 2; DE5 = BZR config 14; digitised to NUTS3 | [[ENTSO-E 2025 BZR Report]] p. 6-8; digitisation method open (O4) | medium |
| A10 | Redispatch compensation | cost-based: up paid at marginal cost, down refunds avoided marginal cost; RES curtailment compensated (transfer, not resource cost) | German practice; [[Cost-Based Redispatch Compensation]]; legal source to hold | medium |
| A11 | Redispatch pool / frictions | open (O1) | Decides H1 ([[Research Design#Why A and C differ at all]]) | - |
| A12 | Demand regionalisation | ENTSO-E hourly DE-LU load × static NUTS3 shares (DemandRegio/FfE if accessible, else population + industrial employment) | **Weakest layer**: no hourly nodal demand is published | medium |
| A13 | Cross-border | fixed historical 2024 hourly physical net exchange per border (ENTSO-E), identical in A/B/C | Isolates intra-DE design effects; ignores loop flows through neighbours | medium |
| A14 | Fuel & CO2 prices | 2024 monthly/daily averages, cited (to cite: EEX/ICE via a public source, EU ETS) | to cite | - |
| A15 | Investment cost & WACC | DEA catalogue or PyPSA technology-data (pinned); WACC [to decide] | to cite | - |
| A16 | Demand | inelastic, no lost load (VoLL as slack only, cost reported) | Standard; same as [[Knoerr Bichler Dobos 2025]] (p. 10) | stated |
