"""Parse the MaStR bulk export (Gesamtdatenexport zip) into one units table.

Own streaming parser instead of open-mastr's database import: open-mastr 1.0.0 fails on the
2026-11-03 export for every EinheitenSolar file and for EinheitenVerbrennung ("Failed to parse
string: '709 712' as int64": fields now hold space-separated catalogue lists; log in
data/raw/mastr/logs/open_mastr.log). We read only the fields we need, keep list fields as text,
and resolve catalogue codes with Katalogwerte.xml. The zip itself was downloaded from
https://download.marktstammdatenregister.de/Gesamtdatenexport_20261103_26.2.zip
(licence DL-DE-BY-2.0, (c) Bundesnetzagentur).
"""

from __future__ import annotations

import re
import sys
import zipfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from xml.etree.ElementTree import iterparse

import pandas as pd

from netzfix.config import DATA_PROCESSED, DATA_RAW
from netzfix.data.download import append_manifest

ZIP = DATA_RAW / "mastr" / "data" / "xml_download" / "Gesamtdatenexport_20261103.zip"
ZIP_URL = "https://download.marktstammdatenregister.de/Gesamtdatenexport_20261103_26.2.zip"

TABLES = {  # XML file stem -> record tag
    "EinheitenSolar": "EinheitSolar",
    "EinheitenWind": "EinheitWind",
    "EinheitenBiomasse": "EinheitBiomasse",
    "EinheitenWasser": "EinheitWasser",
    "EinheitenVerbrennung": "EinheitVerbrennung",
    "EinheitenKernkraft": "EinheitKernkraft",
    "EinheitenGeothermieGrubengasDruckentspannung": "EinheitGeothermieGrubengasDruckentspannung",
    "EinheitenStromSpeicher": "EinheitStromSpeicher",
}
FIELDS = (
    "EinheitMastrNummer", "NameStromerzeugungseinheit", "NameKraftwerk", "EinheitBetriebsstatus",
    "Inbetriebnahmedatum", "DatumEndgueltigeStilllegung", "DatumBeginnVoruebergehendeStilllegung",
    "DatumWiederaufnahmeBetrieb", "Energietraeger", "Hauptbrennstoff", "Technologie",
    "WindAnLandOderAufSee", "ArtDerWasserkraftanlage", "Bruttoleistung", "Nettonennleistung",
    "Laengengrad", "Breitengrad", "Postleitzahl", "Gemeindeschluessel", "Land",
    "LokationMaStRNummer", "SpeMastrNummer",
)
CATALOGUE_FIELDS = ("EinheitBetriebsstatus", "Energietraeger", "Hauptbrennstoff", "Technologie",
                    "WindAnLandOderAufSee", "ArtDerWasserkraftanlage", "Land")


def _members(z: zipfile.ZipFile, stem: str) -> list[str]:
    pat = re.compile(rf"^{stem}(_\d+)?\.xml$")
    return sorted(n for n in z.namelist() if pat.match(n))


def _parse_member(args: tuple[str, str, str]) -> pd.DataFrame:
    zip_path, member, tag = args
    rows = []
    with zipfile.ZipFile(zip_path) as z, z.open(member) as fh:
        rec: dict[str, str] = {}
        for _, el in iterparse(fh, events=("end",)):
            name = el.tag
            if name == tag:
                rows.append(rec)
                rec = {}
                el.clear()
            elif name in FIELDS:
                rec[name] = el.text
    df = pd.DataFrame(rows, columns=list(FIELDS))
    df["table"] = member.split("_")[0].removesuffix(".xml")
    return _compact(df)


def _compact(df: pd.DataFrame) -> pd.DataFrame:
    """Typed, smaller frame: numbers as float, dates as datetime, names only for units >= 1 MW."""
    for c in ("Bruttoleistung", "Nettonennleistung", "Laengengrad", "Breitengrad"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ("Inbetriebnahmedatum", "DatumEndgueltigeStilllegung",
              "DatumBeginnVoruebergehendeStilllegung", "DatumWiederaufnahmeBetrieb"):
        df[c] = pd.to_datetime(df[c], errors="coerce")
    small = df.Bruttoleistung.fillna(0) < 1000  # kW
    df.loc[small, ["NameStromerzeugungseinheit", "NameKraftwerk"]] = None
    df = df.drop(columns=["LokationMaStRNummer", "SpeMastrNummer", "Postleitzahl"])
    for c in ("EinheitBetriebsstatus", "Energietraeger", "Hauptbrennstoff", "Technologie",
              "WindAnLandOderAufSee", "ArtDerWasserkraftanlage", "Land", "table"):
        df[c] = df[c].astype("category")
    return df


def catalogue(z: zipfile.ZipFile) -> dict[str, str]:
    with z.open("Katalogwerte.xml") as fh:
        out, cur = {}, {}
        for _, el in iterparse(fh, events=("end",)):
            if el.tag in ("Id", "Wert"):
                cur[el.tag] = el.text
            elif el.tag == "Katalogwert":
                out[cur["Id"]] = cur.get("Wert")
                cur = {}
                el.clear()
    return out


def _decode(value: str | None, cat: dict[str, str]) -> str | None:
    if value is None:
        return None
    return "|".join(cat.get(v, v) for v in value.split())


def parse(workers: int = 12) -> Path:
    if not ZIP.exists():
        raise FileNotFoundError(f"{ZIP} missing; run `python -m netzfix.data.mastr` to download it")
    with zipfile.ZipFile(ZIP) as z:
        cat = catalogue(z)
        jobs = [(str(ZIP), m, tag) for stem, tag in TABLES.items() for m in _members(z, stem)]
    print(f"{len(jobs)} XML files", flush=True)
    parts = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for k, df in enumerate(ex.map(_parse_member, jobs), 1):
            parts.append(df)
            print(f"  {k}/{len(jobs)} {jobs[k - 1][1]}: {len(df):,} units", flush=True)
    units = pd.concat(parts, ignore_index=True)
    for c in CATALOGUE_FIELDS:
        codes = units[c].astype("object")
        lookup = {v: _decode(v, cat) for v in codes.dropna().unique()}
        units[c] = codes.map(lookup).astype("category")
    units["table"] = units["table"].astype("category")
    out = DATA_PROCESSED / "mastr_units_20261103.parquet"
    units.to_parquet(out)
    return out


def download(url: str = ZIP_URL, retries: int = 30) -> Path:
    """Resumable download of the bulk zip (the MaStR server resets long connections).

    The export is replaced daily; ZIP_URL pins the 2026-11-03 file used for the 2024 baseline.
    If it is no longer online, a newer export can be used; the 2024 filter is date-based.
    """
    import time

    import requests

    from netzfix.data.download import USER_AGENT

    if ZIP.exists():
        return ZIP
    part = ZIP.with_suffix(".zip.part")
    part.parent.mkdir(parents=True, exist_ok=True)
    total = int(requests.head(url, headers={"User-Agent": USER_AGENT}, timeout=60)
                .headers["Content-Length"])
    for attempt in range(retries):
        have = part.stat().st_size if part.exists() else 0
        if have >= total:
            break
        try:
            hdr = {"User-Agent": USER_AGENT, "Range": f"bytes={have}-"}
            with requests.get(url, headers=hdr, stream=True, timeout=120) as r:
                r.raise_for_status()
                with open(part, "ab") as fh:
                    for chunk in r.iter_content(1 << 22):
                        fh.write(chunk)
        except requests.RequestException:
            time.sleep(min(60, 2**attempt))
    if part.stat().st_size != total:
        raise RuntimeError(f"MaStR download incomplete: {part.stat().st_size} of {total} bytes")
    part.replace(ZIP)
    return ZIP


def register_zip() -> None:
    """Append the bulk zip to data/MANIFEST.csv (once)."""
    manifest = (DATA_RAW.parent / "MANIFEST.csv").read_text(encoding="utf-8")
    if "Gesamtdatenexport_20261103" not in manifest:
        append_manifest(ZIP_URL, ZIP, "vault/data/Marktstammdatenregister.md", "DL-DE-BY-2.0",
                        "MaStR Gesamtdatenexport 2026-11-03 (version 26.2), full zip")


if __name__ == "__main__":
    download()
    register_zip()
    p = parse(int(sys.argv[1]) if len(sys.argv) > 1 else 12)
    u = pd.read_parquet(p)
    print(p, len(u))
    print(u.groupby("table").size().to_string())
