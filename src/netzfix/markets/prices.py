"""Price layer (A29) and plant marginal costs (A30).

`price_table` returns hourly input prices for a chosen price set:
- "2024_validation": frozen values from held sources (config `prices.sets.2024_validation`);
- "latest": newest values from free sources that can be fetched by script (electricity
  day-ahead from Energy-Charts; EUA from the DEHSt monthly auction report); fuels without a free
  source must be given in `prices.sets.user`;
- "user": hand-set scenario values (`prices.sets.user`), never presented as data.
Every fetch is cached in data/raw/prices/ with a MANIFEST row (download.fetch).
Marginal cost (EUR/MWh_el) = fuel/eta + CO2 * EF * 0.0036 / eta + VOM  (EF in t CO2/TJ;
0.0036 TJ per MWh).
"""

from __future__ import annotations

import re
from typing import Any

import numpy as np
import pandas as pd

from netzfix.config import DATA_RAW, load_config

TJ_PER_MWH = 0.0036
FUELS = ("gas", "hard_coal", "lignite", "oil")


class MissingPrice(ValueError):
    pass


def _expand(value: Any, index: pd.DatetimeIndex, name: str) -> np.ndarray:
    """Scalar -> constant; 12 values -> by month (Europe/Berlin); None -> MissingPrice."""
    if value is None:
        raise MissingPrice(f"no price for {name!r} in this price set")
    v = np.asarray(value, dtype="float64")
    if v.ndim == 0:
        return np.full(len(index), float(v))
    if v.shape == (12,):
        return v[index.tz_convert("Europe/Berlin").month.to_numpy() - 1]
    raise ValueError(f"{name}: expected a scalar or 12 monthly values, got shape {v.shape}")


def price_table(
    index: pd.DatetimeIndex,
    price_set: str | None = None,
    cfg: dict | None = None,
    required: tuple[str, ...] = (),
) -> pd.DataFrame:
    """Hourly prices: co2 (EUR/t) and fuels (EUR/MWh_th). Missing fuels are NaN unless listed
    in `required` (then MissingPrice is raised)."""
    cfg = cfg or load_config()
    pc = cfg["prices"]
    name = price_set or pc["set"]
    if name == "latest":
        base = {**latest_values(), **(pc["sets"].get("user") or {})}
    else:
        base = dict(pc["sets"][name] or {})
    out = pd.DataFrame(index=index)
    for col, key in [("co2", "co2_eur_t")] + [(f, f"{f}_eur_mwh_th") for f in FUELS]:
        try:
            out[col] = _expand(base.get(key), index, key)
        except MissingPrice:
            if col in required:
                raise
            out[col] = np.nan
    out.attrs["price_set"] = name
    return out


def marginal_cost(tech: dict, prices: pd.DataFrame) -> np.ndarray:
    """EUR/MWh_el per hour for one technology dict (fuel, eta, vom, ef_t_tj)."""
    fuel = prices[tech["fuel"]].to_numpy(dtype="float64")
    co2 = prices["co2"].to_numpy(dtype="float64")
    eta = float(tech["eta"])
    return fuel / eta + co2 * float(tech["ef_t_tj"]) * TJ_PER_MWH / eta + float(tech["vom"])


# ------------------------------------------------------------------ "latest" adapters
DEHST_MONTHLY = (
    "https://www.dehst.de/SharedDocs/downloads/EN/auctioning/{y}/"
    "{y}_report_{m:02d}.pdf?__blob=publicationFile"
)
_DEHST_AVG = re.compile(r"average price per allowance of\s*€\s*([0-9]+[.,][0-9]+)")


def parse_dehst_average(text: str) -> float:
    """Volume-weighted average EUA price from a DEHSt auction report's text."""
    m = _DEHST_AVG.search(text)
    if not m:
        raise ValueError("no 'average price per allowance' found in DEHSt report")
    return float(m.group(1).replace(",", "."))


def latest_eua(today: pd.Timestamp | None = None, max_back: int = 4) -> tuple[float, str]:
    """Most recent DEHSt monthly report (tries this month and up to `max_back` before)."""
    import requests
    from pypdf import PdfReader

    from netzfix.data.download import USER_AGENT, DownloadError, append_manifest

    t = (today or pd.Timestamp.now(tz="Europe/Berlin")).to_period("M")
    for k in range(max_back + 1):
        p = t - k
        url = DEHST_MONTHLY.format(y=p.year, m=p.month)
        path = DATA_RAW / "prices" / "dehst" / f"{p.year}_{p.month:02d}_report.pdf"
        if not path.exists():
            # unpublished months return an HTML page with HTTP 200: accept only real PDFs
            try:
                r = requests.get(url, timeout=60, headers={"User-Agent": USER_AGENT})
            except requests.RequestException:
                continue
            if r.status_code != 200 or not r.content.startswith(b"%PDF"):
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(r.content)
            append_manifest(
                url,
                path,
                source_note="vault/literature/DEHSt 2024 Auctioning Reports.md",
                license="DEHSt / UBA publication",
                notes=f"monthly EUA auction report {p}",
            )
        text = "".join(pg.extract_text() or "" for pg in PdfReader(path).pages[:8])
        return parse_dehst_average(text), str(p)
    raise DownloadError("no DEHSt monthly report found in the last months")


def latest_values() -> dict:
    """Prices for the "latest" set that a free source provides (currently EUA only)."""
    co2, month = latest_eua()
    return {"co2_eur_t": co2, "_co2_month": month}
