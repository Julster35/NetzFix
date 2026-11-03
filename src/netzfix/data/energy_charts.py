"""Cross-border physical flows of Germany from the Energy-Charts API (Fraunhofer ISE).

Endpoint `/cbpf?country=de` (read 2026-11-03): physical flows in GW between Germany and each
neighbour, 15-minute resolution, positive = import into Germany. Licence per the API docs:
"Unless stated otherwise, the data provided by the Energy-Charts API is licensed under the
CC BY 4.0 license" (https://api.energy-charts.info, openapi info). Attribution: Energy-Charts.info,
Fraunhofer ISE.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from netzfix.config import DATA_PROCESSED, DATA_RAW
from netzfix.data.download import fetch

API = "https://api.energy-charts.info/cbpf"
NAME_TO_ISO = {
    "Austria": "AT", "Belgium": "BE", "Czech Republic": "CZ", "Denmark": "DK", "France": "FR",
    "Luxembourg": "LU", "Netherlands": "NL", "Norway": "NO", "Poland": "PL", "Sweden": "SE",
    "Switzerland": "CH",
}


def _month(year: int, m: int) -> Path:
    start = pd.Timestamp(year=year, month=m, day=1, tz="Europe/Berlin")
    end = start + pd.offsets.MonthBegin(1)
    url = (f"{API}?country=de&start={start.isoformat().replace('+', '%2B')}"
           f"&end={end.isoformat().replace('+', '%2B')}")
    return fetch(url, DATA_RAW / "energy_charts" / f"cbpf_de_{year}_{m:02d}.json",
                 source_note="vault/data/ENTSO-E Transparency.md", license="CC-BY-4.0",
                 notes="Energy-Charts (Fraunhofer ISE) cross-border physical flows, GW, +import")


def build_year(year: int = 2024) -> Path:
    """Hourly MW per neighbour (+ = import into DE), UTC index, same hours as SMARD."""
    parts = []
    for m in range(1, 13):
        d = json.loads(_month(year, m).read_text(encoding="utf-8"))
        idx = pd.to_datetime(d["unix_seconds"], unit="s", utc=True)
        parts.append(pd.DataFrame({NAME_TO_ISO[c["name"]]: c["data"] for c in d["countries"]
                                   if c["name"] in NAME_TO_ISO}, index=idx))
    df = pd.concat(parts)
    df = df[~df.index.duplicated()].sort_index().astype(float) * 1000.0      # GW -> MW
    hourly = df.resample("h").mean()
    lo = pd.Timestamp(f"{year}-01-01", tz="Europe/Berlin").tz_convert("UTC")
    hi = pd.Timestamp(f"{year + 1}-01-01", tz="Europe/Berlin").tz_convert("UTC")
    hourly = hourly[(hourly.index >= lo) & (hourly.index < hi)]
    hourly.index.name = "snapshot_utc"
    out = DATA_PROCESSED / f"cbpf_DE_{year}.parquet"
    hourly.to_parquet(out)
    return out


if __name__ == "__main__":
    p = build_year(2024)
    h = pd.read_parquet(p)
    print(p, h.shape, "missing hours per country:", h.isna().sum().to_dict())
    print("net import TWh by country (+ = import):", (h.sum() / 1e6).round(2).to_dict())
    print("total net physical import TWh:", round(h.sum().sum() / 1e6, 2))
