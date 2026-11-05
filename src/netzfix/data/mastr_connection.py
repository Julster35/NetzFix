"""Connection voltage stated in MaStR grid-connection-point names (assumption A35).

MaStR's `Spannungsebene` only says "Höchstspannung" (no 220/380 split). Some operators name the
connection point with the voltage, e.g. "380-kV Anschluss KW Wilhelmshaven (Onyx)". This module
links units -> Lokation -> Netzanschlusspunkt in the bulk export and keeps units whose connection
point name states exactly one of 220 / 380 kV. Solar tables are skipped (no EHV-connected units of
relevance; they are also the bulk of the export).
Writes data/processed/mastr_connection_kv.csv (unit, kv, nap_name).
"""

from __future__ import annotations

import re
import zipfile

import pandas as pd

from netzfix.config import DATA_PROCESSED, DATA_RAW

EXPORT = DATA_RAW / "mastr" / "data" / "xml_download" / "Gesamtdatenexport_20261103.zip"
OUT = DATA_PROCESSED / "mastr_connection_kv.csv"
UNIT_TABLES = re.compile(r"Einheiten(Verbrennung|Wasser|Biomasse|StromSpeicher|Wind|Kernkraft|"
                         r"GeothermieGrubengasDruckentspannung)")
KV = re.compile(r"\b(220|380)\s*-?\s*kV\b", re.I)


def _read(z: zipfile.ZipFile, name: str) -> str:
    return z.read(name).decode("utf-16")


def build() -> pd.DataFrame:
    z = zipfile.ZipFile(EXPORT)
    lok: dict[str, str] = {}
    for n in z.namelist():
        if not UNIT_TABLES.match(n):
            continue
        s = _read(z, n)
        for m in re.finditer(r"<EinheitMastrNummer>(SEE\d+)</EinheitMastrNummer>.*?"
                             r"<LokationMaStRNummer>(SEL\d+)</LokationMaStRNummer>", s, re.S):
            lok[m.group(1)] = m.group(2)
    locs = set(lok.values())
    nap: dict[str, list[str]] = {}
    for n in z.namelist():
        if not n.startswith("Netzanschlusspunkte"):
            continue
        for r in re.findall(r"<Netzanschlusspunkt>(.*?)</Netzanschlusspunkt>", _read(z, n), re.S):
            loc = re.search(r"<LokationMaStRNummer>(\w+)<", r)
            if not loc or loc.group(1) not in locs:
                continue
            texts = [m.group(1) for m in re.finditer(
                r"<(?:NetzanschlusspunktBezeichnung|NameDerTechnischenLokation)>([^<]*)<", r)]
            nap.setdefault(loc.group(1), []).extend(texts)
    rows = []
    for unit, loc in lok.items():
        texts = nap.get(loc, [])
        kvs = {int(k) for t in texts for k in KV.findall(t)}
        if len(kvs) == 1:
            rows.append({"unit": unit, "kv": kvs.pop(), "nap_name": " | ".join(sorted(set(texts)))})
    out = pd.DataFrame(rows, columns=["unit", "kv", "nap_name"]).sort_values("unit")
    out.to_csv(OUT, index=False)
    return out


if __name__ == "__main__":
    d = build()
    print(OUT, len(d), d.kv.value_counts().to_dict())
