---
type: data-source
date: 2026-11-03
tags: [data, mastr, units, capacities]
ai-first: true
status: "not accessed yet (2026-11-03)"
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

## Known issues (to check)
- Small units often have only postcode-level location; coordinates missing for privacy below some size. `medium`
