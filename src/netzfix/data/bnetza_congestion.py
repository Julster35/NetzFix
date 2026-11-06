"""BNetzA lists of overloaded transmission-grid elements ("Überlastete Netzelemente der ÜNB").

Real yardstick for where the grid is congested (T7, vault/project/Validation.md). Sources:
- 2023: BNetzA quarterly reports Netzengpassmanagement Q1-Q4 2023 (PDF), table "Überlastete
  Netzelemente der ÜNB" (element name, control area, overload duration in hours, based on the
  TSOs' operational planning process PRD1).
- 2024: SMARD topic articles for Q1 and Q2 2024 publish the same table as xlsx. No Q3/Q4 2024
  table was found on SMARD or bundesnetzagentur.de (checked 2026-11-06).

Files are cached in data/raw/bnetza/congestion/ and recorded in data/MANIFEST.csv.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from netzfix.config import DATA_PROCESSED, DATA_RAW
from netzfix.data.download import fetch

_DSC = ("https://dsc.bund.de/SharedDocs/Downloads/DE/Sachgebiete/Energie/"
        "Unternehmen_Institutionen/Versorgungssicherheit/Engpassmanagement/")
_BNA = ("https://data.bundesnetzagentur.de/Bundesnetzagentur/SharedDocs/Downloads/DE/Sachgebiete/"
        "Energie/Unternehmen_Institutionen/Versorgungssicherheit/Engpassmanagement/")
_SMARD = "https://www.smard.de/resource/blob/"

SOURCES: dict[str, str] = {
    "2023_Q1.pdf": _DSC + "QuartalszahlenQ1in2023.pdf",
    "2023_Q2.pdf": _DSC + "QuartalszahlenQ2_2023.pdf",
    "2023_Q3.pdf": _BNA + "Q3_2023_Quartalsbericht_Netzengpassmanagement.pdf",
    "2023_Q4.pdf": _DSC + "QuartalszahlenQ4_2023.pdf",
    "2024_Q1.xlsx": _SMARD + "213846/db0e59d6881e7a91a9fdb89390945ba3/"
                    "ueberlastete-netzelemente-der-uenb-q1-2024-data.xlsx",
    "2024_Q2.xlsx": _SMARD + "215142/aba3a7ed84ff102a2ee835d48303e4b6/"
                    "ueberlastete-netzelemente-der-uenb-q2-2024-data.xlsx",
}

RAW_DIR = DATA_RAW / "bnetza" / "congestion"
NOTE = "vault/data/BNetzA Overloaded Grid Elements.md"
LICENCE = "BNetzA / SMARD publication (SMARD data CC BY 4.0; to confirm for reports)"


OUT = DATA_PROCESSED / "bnetza_overloaded_elements.csv"
_ROW = re.compile(r"^(?P<el>.+?)\s+(?P<cz>(?:50Hertz|TenneT|Amprion|TransnetBW)"
                  r"(?:\s*/\s*(?:50Hertz|TenneT|Amprion|TransnetBW))*)\s+(?P<h>\d{1,3}(?:\.\d{3})*)\s*$")


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", str(s)).strip()


def _from_pdf(path: Path) -> list[dict]:
    from pypdf import PdfReader

    for page in PdfReader(path).pages:
        t = page.extract_text() or ""
        if "Dauer in Stunden" not in t:
            continue
        rows = []
        body = t.split("Dauer in Stunden", 1)[1].split("Quelle:", 1)[0]
        for line in body.splitlines():
            m = _ROW.match(_clean(line))
            if m:
                rows.append({"element": _clean(m["el"]), "control_area": _clean(m["cz"]),
                             "hours": int(m["h"].replace(".", ""))})
        if rows:
            return rows
    raise ValueError(f"no table 'Dauer in Stunden' in {path}")


def _from_xlsx(path: Path) -> list[dict]:
    d = pd.read_excel(path, header=None)
    has_hdr = d.apply(lambda r: r.astype(str).str.contains("Dauer in Stunden").any(), axis=1)
    hdr = d.index[has_hdr][0]
    rows = []
    for _, r in d.loc[hdr + 1:].iterrows():
        v = [x for x in r.tolist() if pd.notna(x)]
        if len(v) >= 4 and isinstance(v[0], (int, float)):
            rows.append({"element": _clean(v[1]), "control_area": _clean(v[2]),
                         "hours": int(v[3])})
    return rows


def parse() -> pd.DataFrame:
    """One row per (year, quarter, rank): element name as published, control area, hours."""
    out = []
    for name in SOURCES:
        p = RAW_DIR / name
        year, q = name.split(".")[0].split("_")
        rows = _from_pdf(p) if p.suffix == ".pdf" else _from_xlsx(p)
        for i, r in enumerate(rows, 1):
            out.append({"year": int(year), "quarter": int(q[1]), "rank": i, **r,
                        "source_file": p.relative_to(DATA_RAW).as_posix()})
    df = pd.DataFrame(out)
    df.to_csv(OUT, index=False, encoding="utf-8")
    return df


def fetch_all() -> list[Path]:
    out = []
    for name, url in SOURCES.items():
        q = name.split(".")[0].replace("_", " ")
        out.append(fetch(url, RAW_DIR / name, source_note=NOTE, license=LICENCE,
                         notes=f"Ueberlastete Netzelemente der UENB, {q} (BNetzA)"))
    return out


if __name__ == "__main__":
    for p in fetch_all():
        print(p)
    print(parse().groupby(["year", "quarter"]).size())
