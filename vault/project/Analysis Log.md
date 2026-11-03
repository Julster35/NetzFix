---
type: log
date: 2026-11-03
tags: [analysis-log, specifications]
ai-first: true
---

# Analysis Log

## For future agent
Every specification that is run gets one entry here, **before** its result is looked at, and whatever the result (including failures and smoke tests). The result line is filled in afterwards with script, results file and commit. Together with the frozen [[Hypotheses]] and the OpenTimestamps anchors (`timestamps/`) this lets the write-up show how many specifications were tried. Newest at the bottom.

Entry template:
```
### YYYY-MM-DD - short name
- Scenario: (design A/B/C, zone map, year, weather year, buses, resolution, line rating, solver)
- Inputs: (data versions / MANIFEST rows)
- Output metric:
- Result: (numbers) - script, results file, commit
- Why run / what changed vs previous:
```

---

(no entries yet - the first is planned as Milestone 1's smoke test)
