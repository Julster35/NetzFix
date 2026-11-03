---
type: data-source
date: 2026-11-03
tags: [data, cross-border, physical-flows, fraunhofer-ise]
ai-first: true
status: "2024 cross-border physical flows downloaded 2026-11-03 (public API, no key, CC BY 4.0)"
---

# Energy-Charts

## For future agent
Fraunhofer ISE's Energy-Charts API supplies the measured hourly physical flows between Germany and each of its 11 neighbours, without an account. NetzFix uses them (since 2026-11-03) as the fixed exchange at the neighbour equivalents, replacing the v0 split of SMARD's residual by line capacity. Code: `src/netzfix/data/energy_charts.py`.

## Access `stated`
- Endpoint: `https://api.energy-charts.info/cbpf?country=de&start=...&end=...` (read 2026-11-03): "Returns the cross-border physical flows (cbpfs) of electricity in GW between a specified country and its neighbors. Positive values indicate an import of electricity, whereas negative values show electricity exports."
- Resolution 15 min; NetzFix averages to hourly MW (UTC), aligned with SMARD.
- Licence (API docs, openapi info): "Unless stated otherwise, the data provided by the Energy-Charts API is licensed under the CC BY 4.0 license." Attribution: Energy-Charts.info, Fraunhofer ISE. The upstream source is not named in the API response (presumably ENTSO-E; not verified).

## 2024 values `stated` (from `data/processed/cbpf_DE_2024.parquet`)
- 8,784 hours, no gaps, 11 countries.
- Net import TWh (+ import / - export): FR +19.77, DK +7.40, NO +5.78, CH +4.49, BE +2.70, SE +2.62, NL -0.05, AT -2.09, LU -2.81, CZ -3.87, PL -8.81. Total **+25.14 TWh**.
- Compare: commercial net import 27.3 TWh ([[BNetzA BKartA 2025 Monitoringbericht]] p. 23); SMARD load + pumped load - generation 40.9 TWh ([[SMARD]]). The 15.8 TWh difference to SMARD is treated as unmetered domestic supply ([[Assumptions]] A21b).
