"""Rebuild vault/index.md: every note by folder, with the first sentence of its "For future agent".

Usage: uv run python scripts/build_index.py
Hand-written one-liners can replace the generated ones; re-running overwrites them, so edit the
note's "For future agent" section instead.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

VAULT = Path(__file__).resolve().parents[1] / "vault"
SECTIONS = [
    ("Root", "."),
    ("Project", "project"),
    ("Concepts", "concepts"),
    ("Literature", "literature"),
    ("Data sources", "data"),
    ("Figures", "figures"),
    ("Inputs", "inputs"),
    ("Outbox", "outbox"),
]
SKIP = {"index.md", "log.md", "_CLAUDE.md"}


def first_sentence(path: Path, limit: int = 220) -> str:
    text = path.read_text(encoding="utf-8")
    m = re.search(r"## For future agent\s*\n(.+?)(?:\n\s*\n|\Z)", text, re.S)
    if not m:
        quote = re.search(r"^>\s*\*?(.+?)\*?\s*$", text, re.M)
        return "Dashboard: " + quote.group(1) if quote else "(no For-future-agent section)"
    para = " ".join(m.group(1).split())
    sent = re.split(r"(?<=[.!?])\s+(?=[A-Z*\[])", para)[0]
    return sent if len(sent) <= limit else sent[: limit - 3].rstrip() + "..."


def main() -> None:
    n_pdfs = len(list((VAULT / "literature" / "pdfs").glob("*.pdf")))
    lines = [
        "---",
        "type: index",
        f"date: {date.today().isoformat()}",
        "tags: [index, catalog]",
        "ai-first: true",
        "---",
        "",
        "# NetzFix - Vault Index",
        "",
        "Catalog of every note, grouped by folder. Read this before searching. "
        f"PDFs: `literature/pdfs/` ({n_pdfs} files as of {date.today().isoformat()}). "
        "Built by `scripts/build_index.py`.",
        "",
    ]
    for title, folder in SECTIONS:
        notes = sorted(p for p in (VAULT / folder).glob("*.md") if p.name not in SKIP)
        if not notes:
            continue
        lines += [f"## {title} ({len(notes)})", ""]
        lines += [f"- [[{p.stem}]] - {first_sentence(p)}" for p in notes]
        lines.append("")
    (VAULT / "index.md").write_text("\n".join(lines), encoding="utf-8")
    print("index.md:", sum(1 for line in lines if line.startswith("- [[")), "notes")


if __name__ == "__main__":
    main()
