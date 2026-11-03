"""SMARD (Bundesnetzagentur) hourly market data for Germany, via the public chart_data API.

Endpoints and filter IDs: OpenAPI spec of bundesAPI/smard-api (read 2026-11-03,
https://github.com/bundesAPI/smard-api). Data are delivered in weekly JSON chunks; timestamps are
epoch milliseconds (UTC instant of the local hour start). Values: MWh per hour for energy series,
EUR/MWh for prices. Licence: CC BY 4.0 per smard.de (to confirm on the site; see vault data note).
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import requests

from netzfix.config import DATA_PROCESSED, DATA_RAW
from netzfix.data.download import USER_AGENT, fetch

BASE = "https://www.smard.de/app/chart_data"

# filter id -> short name (from the bundesAPI spec)
FILTERS = {
    410: "load",                 # Stromverbrauch: Gesamt (Netzlast)
    1223: "lignite",             # Braunkohle
    1224: "nuclear",             # Kernenergie
    1225: "wind_offshore",
    1226: "hydro",               # Wasserkraft
    1227: "other_conventional",  # Sonstige Konventionelle
    1228: "other_renewable",     # Sonstige Erneuerbare
    4066: "biomass",
    4067: "wind_onshore",
    4068: "solar",               # Photovoltaik
    4069: "hard_coal",           # Steinkohle
    4070: "pumped_hydro",        # Pumpspeicher (generation)
    4071: "gas",                 # Erdgas
    4387: "pumped_hydro_load",   # Stromverbrauch: Pumpspeicher
    4169: "price_de_lu",         # Marktpreis DE/LU, EUR/MWh
}


def _week_starts(filt: int, region: str) -> list[int]:
    r = requests.get(f"{BASE}/{filt}/{region}/index_hour.json",
                     headers={"User-Agent": USER_AGENT}, timeout=60)
    r.raise_for_status()
    return r.json()["timestamps"]


def series(filt: int, year: int, region: str = "DE") -> pd.Series:
    """Hourly series for one filter and calendar year (Europe/Berlin), cached in data/raw/smard."""
    start = pd.Timestamp(f"{year}-01-01", tz="Europe/Berlin")
    end = pd.Timestamp(f"{year + 1}-01-01", tz="Europe/Berlin")
    week = pd.Timedelta(days=7)
    parts = []
    for ts in _week_starts(filt, region):
        t = pd.Timestamp(ts, unit="ms", tz="UTC")
        if t + week < start or t >= end:
            continue
        name = f"{filt}_{region}_hour_{ts}.json"
        path = fetch(f"{BASE}/{filt}/{region}/{name}", DATA_RAW / "smard" / name,
                     source_note="vault/data/SMARD.md", license="CC-BY-4.0 (to confirm)",
                     notes=f"SMARD filter {filt} ({FILTERS.get(filt, '?')}), weekly chunk")
        data = json.loads(Path(path).read_text(encoding="utf-8"))["series"]
        parts.append(pd.Series({pd.Timestamp(a, unit="ms", tz="UTC"): b for a, b in data}))
    s = pd.concat(parts).sort_index()
    s = s[~s.index.duplicated()].tz_convert("Europe/Berlin")
    s = s[(s.index >= start) & (s.index < end)].astype("float64")
    s.name = FILTERS.get(filt, str(filt))
    return s


def build_year(year: int = 2024, region: str = "DE") -> Path:
    """All FILTERS for one year into data/processed/smard_<region>_<year>.parquet (UTC index)."""
    df = pd.concat([series(f, year, region) for f in FILTERS], axis=1)
    df.index = df.index.tz_convert("UTC")
    df.index.name = "snapshot_utc"
    out = DATA_PROCESSED / f"smard_{region}_{year}.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out)
    return out


if __name__ == "__main__":
    p = build_year(2024)
    df = pd.read_parquet(p)
    print(p, df.shape)
    print(df.isna().sum().to_string())
    print((df.drop(columns="price_de_lu").sum() / 1e6).round(2).to_string())  # TWh
