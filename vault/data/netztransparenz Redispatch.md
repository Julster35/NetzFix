---
type: data-source
date: 2026-11-03
tags: [data, redispatch, validation, tso]
ai-first: true
status: "2024 downloaded 2026-11-05 (12 monthly CSVs, UTC); used for T6"
---

# netztransparenz Redispatch

## For future agent
netztransparenz.de is the joint information platform of the four German TSOs; it publishes individual redispatch measures (time, TSO, affected units or areas, direction, volume). NetzFix uses it to validate the time pattern and volume of design A's redispatch ([[Validation]] V4).

## Use
- Hourly redispatch volume 2024 (up / down) vs design A's redispatch stage; spatial pattern if units/areas are given.

## Access (as of 2026-11-05)
- Page: https://www.netztransparenz.de/de-de/Systemdienstleistungen/Betriebsfuehrung/Redispatch . "Download CSV" is an ASP.NET postback (module ctr2598, Telerik date pickers; data from 2021-01-01; time zone ME(S)Z or UTC). No login. Downloader: `src/netzfix/data/netztransparenz_redispatch.py` (one file per month, checks the returned date range because the server silently falls back to its default range). Archive 2013-2020 as a static ZIP on the same page.
- Columns: BEGINN_DATUM, BEGINN_UHRZEIT, ZEITZONE_VON, ENDE_DATUM, ENDE_UHRZEIT, ZEITZONE_BIS, GRUND_DER_MASSNAHME, RICHTUNG, MITTLERE_LEISTUNG_MW, MAXIMALE_LEISTUNG_MW, GESAMTE_ARBEIT_MWH, ANWEISENDER_UENB, ANFORDERNDER_UENB, BETROFFENE_ANLAGE, PRIMAERENERGIEART. `stated` (file header)
- Scope (page text, 2026-11-05): "tagesscharfe Redispatchmaßnahmen, die Anpassungen von in Deutschland angeschlossen Anlagen betreffen"; cross-border measures only with their German part; system-balance measures excluded. `stated`
- 2024: 17,360 unique rows; reasons incl. current-based redispatch (15,231), current+voltage (412), voltage-only (317), countertrade DE-DK1/DK2/NO2 (570), reserve test runs. Offshore connection points appear as `OWP UW <substation>`, areas as e.g. `EE Niedersachsen`.
- **Licence: not stated on the page** (footer links Impressum / Datenschutz not checked yet). Used internally for validation; check before publishing raw rows.
