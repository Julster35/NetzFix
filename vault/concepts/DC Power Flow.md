---
type: concept
date: 2026-11-03
tags: [power-flow, physics]
ai-first: true
---

# DC Power Flow

## For future agent
The linearised ("DC") power-flow approximation used for all NetzFix network optimisations: flows on AC lines follow from voltage-angle differences, losses and reactive power are ignored, voltages are 1 p.u. It makes the market problems linear programs and gives PTDFs.

## Equations
- f_l = (theta_i - theta_j) / x_l for line l between buses i, j (per unit). `high`
- Equivalent: f = PTDF * p (net injections). PTDFs depend only on topology and reactances. `high`
- HVDC links are controllable (no angle relation) and are modelled as PyPSA `Link`s. `high`

## Limits (to list in the [[Validation]] discussion)
- No losses, no voltage or stability constraints; reactances come from OSM-derived line parameters ([[Xiong et al 2025]] - not yet read in full). `high`
- How PyPSA formulates Kirchhoff's voltage law: check in [[Brown Hoersch Schlachtberger 2018]] before stating. `speculation`
