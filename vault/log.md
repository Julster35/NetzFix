# Vault Operations Log

Append-only record of what Claude does to this vault. One file per day in `Logs/`, named `YYYY-MM-DD.md`. This file is only a pointer - never write entries here.

## Entry template

```markdown
---
type: log
date: YYYY-MM-DD
ai-first: true
---

# YYYY-MM-DD

## For future agent
2-3 sentences: what happened today and where it left the project.

**HH:MM** - action | description
```

Actions in use: `init`, `ingest`, `save`, `spec`, `check`, `result`, `decision`, `infra`, `viz`, `outbox`.
