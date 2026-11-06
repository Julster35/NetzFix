---
type: input
date: 2026-11-06
tags: [input, redispatch, n-1, line-limits, colleague]
ai-first: true
---

# 2026-11-06 Colleague redispatch details

## For future agent
Suggestions from a colleague of Julien's, passed on by Julien on 2026-11-06 (wording below is Julien's). Not a held source: the 120% value has no citation yet, so it may only enter the model as an assumption with its source stated or as a sensitivity, and must not carry a result until backed by a held document.

## Julien's words (verbatim)
> "lines hould not exceed a certrain percaentage of their usage as hard constraint. he chose 120 %, what do we see in the data here? also to simulate, it seems that operators try to have redundancy, so if you have 3 lines load should be distributed in a way, that if one faults, the other two can handle the load, other simulations do that with n-1? if we go one step further we could build each operators, consumers and plants behaviour like the law suggests and what we see in the bahaviour. i think if we rebuild market incentives this could work [...] theres also data for the pricing of overloading a line and so on."

## What we checked the same day (`stated`, from held data)
- [[JAO Core Static Grid Model]] (6th release, 2024-09), German circuits with both a minimum and a maximum weather-dependent rating (DLRmin, DLRmax; 226 of 959 circuits): **DLRmax / DLRmin median 1.24**, IQR 1.16-1.42, 10th-90th percentile 1.09-1.53; median by TSO: 50Hertz 1.26 (6 circuits), Amprion 1.22 (21), TenneT 1.29 (142), TransnetBW 1.20 (57); 220 kV 1.25, 380 kV 1.21. Computed with `netzfix.network.jao_ratings.circuits()`.
- So a limit of about 120% of the base rating is within the range the TSOs themselves state for weather-dependent operation. Whether the colleague's 120% means this, or a temporary post-fault limit under n-1, is open: ask him.

## Open questions to the colleague
1. 120% of which rating (thermal standard rating? seasonal? DLR?) and in which state (normal operation, or after a fault, for how long)? Source?
2. "Pricing of overloading a line": which data (JAO flow-based shadow prices per critical element, netztransparenz calculated prices, TSO cost reports)?

## Links
[[Validation]] (T7, v9) · [[N-1 Security Proxy]] · [[EnWG 13 13a Redispatch]] · [[Next Steps]]
