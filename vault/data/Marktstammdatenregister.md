---
type: data-source
date: 2026-11-03
tags: [data, mastr, units, capacities]
ai-first: true
status: "downloaded and parsed 2026-11-03 (export of that day); baseline 2024 fleet built"
---

# Marktstammdatenregister

## For future agent
The Marktstammdatenregister (MaStR) is the BNetzA's official register of all German generation and storage units with location, capacity and commissioning date. NetzFix takes the full DE fleet from it (state end of 2024), downloaded with `open-mastr` (AGPL-3.0, v1.0.0) in a standalone script, and attaches every unit to its nearest cluster bus. Layer 2, and the weights for layer 3.

## Use
- Conventional, storage and RES units with capacity, carrier, coordinates / postcode, commissioning and decommissioning dates -> fleet as of 2024 ([[Assumptions]] A1).
- RES capacity per bus weights the atlite profiles ([[ERA5 and atlite]]).

## Access
- https://www.marktstammdatenregister.de ; bulk download via https://github.com/OpenEnergyPlatform/open-MaStR (checked 2026-11-03).
- Licence of the data: to record from the MaStR site at download (expected DL-DE-BY-2.0 - verify). `speculation` until checked.
- open-mastr is AGPL: used only in `scripts/download_mastr.py`, not imported by `src/netzfix` ([[Decision Log]] 2026-11-03).

## State (2026-11-03) `stated`
- Bulk zip `Gesamtdatenexport_20261103_26.2.zip`, 3,269,784,561 bytes, from https://download.marktstammdatenregister.de (server resets long connections; resumable download in `netzfix.data.mastr.download`).
- **open-mastr 1.0.0 failed** on this export: every `EinheitenSolar_*.xml` and `EinheitenVerbrennung.xml` raised "Failed to parse string: '709 712' as a scalar of type int64" (catalogue fields now hold space-separated lists). Upstream had no fix on 2026-11-03. We use our own streaming parser (`src/netzfix/data/mastr.py`): 103 files, 9,716,028 units, no errors; open-mastr is not used any more (so no AGPL dependency).
- Large conventional plants have **no coordinates** and only a 5-digit district key in the public export. Coordinates come from powerplantmatching v0.9.1 (CC-BY-4.0, matched by MaStR number, 73.0 GW), see [[Assumptions]] A19a.
- 6,798,004 units operating in at least one month of 2024; fleet per month in [[Playground]].
- Austrian Illwerke hydro/pumped storage (Kops, Vermunt, Obervermunt; ~1.5 GW) are in MaStR (German control area) and placed via powerplantmatching.

## Known issues (to check)
- Small units often have only postcode-level location; coordinates missing for privacy below some size. `medium`
