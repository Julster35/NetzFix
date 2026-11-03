---
type: concept
date: 2026-11-03
tags: [market-design, design-A, redispatch]
ai-first: true
---

# Uniform Pricing and Redispatch

## For future agent
Design **A**: Germany (DE-LU) clears as one bidding zone with one price per hour, ignoring internal grid limits; the transmission operators then fix overloads by **redispatch** (raising units behind a congestion, lowering units in front of it). This is today's German system. In NetzFix it is modelled in two stages on the same network ([[Research Design#A - Uniform + redispatch]]).

## How it works
1. **Market stage:** all DE buses merged into one copper plate; fixed cross-border exchange ([[Assumptions]] A13). Uniform price = dual of the single balance constraint. `high`
2. **Redispatch stage:** the market dispatch is fixed on the full nodal network; up/down adjustments restore feasibility of every line (`s_max_pu`, [[N-1 Security Proxy]]) at least cost, paid under [[Cost-Based Redispatch Compensation]]. `high`

## Why it matters here
- The uniform price carries no location signal, so in A the market value of a unit differs between nodes only through its generation profile ([[Market Value of a Unit]]). `high`
- With an unrestricted pool and costs at marginal cost, A reproduces the nodal cost exactly; the cost gap to [[Nodal Pricing (LMP)]] comes from redispatch frictions ([[Research Design#Why A and C differ at all]]). `stated` (PyPSA example, see [[Prior Art]]), `high` (general)
- Observed scale: German congestion management was 34 TWh and EUR 3.1 bn in 2023 per [[Knoerr Bichler Dobos 2025]] p. 2 (citing Bundesnetzagentur 2024). `stated`
