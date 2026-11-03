---
type: data-source
date: 2026-11-03
tags: [data, era5, atlite, weather, profiles]
ai-first: true
status: "not accessed yet (2026-11-03)"
---

# ERA5 and atlite

## For future agent
Wind and PV hourly capacity factors per cluster bus for weather year 2024 are computed with atlite (MIT, v0.7.0) from ERA5 reanalysis, then weighted by MaStR installed capacity within each cluster. Layer 3. ERA5 download needs a Copernicus CDS account (a login: U1).

## Use
- atlite cutout for DE + neighbours, 2024 -> wind (onshore, offshore) and PV `p_max_pu` per bus, capacity-weighted with [[Marktstammdatenregister]].
- Also profiles for the hypothetical units in [[Market Value of a Unit]].

## Access
- ERA5 via the Copernicus Climate Data Store API (account + key; terms to record). Whether PyPSA-Eur's `atlite.cutouts` offers a prebuilt 2024 cutout: check (U1).
- https://github.com/PyPSA/atlite (checked 2026-11-03).

## Known issues
- ERA5 wind speeds are known to need bias correction for capacity factors; PyPSA-Eur applies correction factors - document what we use. `medium`
