"""Redispatch measures of the four German TSOs from netztransparenz.de (public "Download CSV").

Page (read 2026-11-05): https://www.netztransparenz.de/de-de/Systemdienstleistungen/Betriebsfuehrung/Redispatch
"tagesscharfe Redispatchmaßnahmen, die Anpassungen von in Deutschland angeschlossen Anlagen
betreffen"; cross-border measures only with their German part; system-balance measures excluded.
The download is an ASP.NET postback (Telerik date pickers, module ctr2598): GET the page for the
hidden form state, then POST the form with the date range and the CSV button. One file per month.
"""

from __future__ import annotations

import json
import re
import time
from datetime import date
from html import unescape
from pathlib import Path

import pandas as pd
import requests

from netzfix.config import DATA_RAW
from netzfix.data.download import USER_AGENT, DownloadError, append_manifest

PAGE = "https://www.netztransparenz.de/de-de/Systemdienstleistungen/Betriebsfuehrung/Redispatch"
MOD = "dnn$ctr2598$View$"
RAW = DATA_RAW / "netztransparenz" / "redispatch"


def _hidden_fields(html: str) -> dict[str, str]:
    out = {}
    for tag in re.findall(r"<input[^>]*>", html):
        name = re.search(r'name="([^"]+)"', tag)
        if not name or 'type="hidden"' not in tag:
            continue
        val = re.search(r'value="([^"]*)"', tag)
        out[unescape(name.group(1))] = unescape(val.group(1)) if val else ""
    return out


def _post_month(s: requests.Session, start: date, end: date, tz: str) -> bytes:
    page = s.get(PAGE, timeout=60)
    page.raise_for_status()
    form = _hidden_fields(page.text)
    cid = MOD.replace("$", "_")
    form.update({
        "__EVENTTARGET": f"{MOD}DownloadCSVButton", "__EVENTARGUMENT": "",
        f"{cid}DownloadCSVButton_ClientState": "",
        f"{MOD}cbbDownloadTimZone": "UTC" if tz == "UTC" else "ME(S)Z",
        f"{cid}cbbDownloadTimZone_ClientState": json.dumps(
            {"logEntries": [], "value": tz, "text": "UTC" if tz == "UTC" else "ME(S)Z",
             "enabled": True, "checkedIndices": [], "checkedItemsTextOverflows": False}),
    })
    for name, d in (("FromDatePicker", start), ("ToDatePicker", end)):
        stamp = d.strftime("%Y-%m-%d-00-00-00")
        form[f"{MOD}{name}"] = d.isoformat()
        form[f"{MOD}{name}$dateInput"] = d.strftime("%d.%m.%Y")
        form[f"{cid}{name}_dateInput_ClientState"] = json.dumps(
            {"enabled": True, "emptyMessage": "", "validationText": stamp,
             "valueAsString": stamp, "minDateStr": "2021-01-01-00-00-00",
             "maxDateStr": "2099-12-31-00-00-00",
             "lastSetTextBoxValue": d.strftime("%d.%m.%Y")})
    files = {k: (None, v) for k, v in form.items()}        # form is multipart/form-data
    r = s.post(PAGE, files=files, timeout=180)
    r.raise_for_status()
    ctype = r.headers.get("Content-Type", "")
    if "html" in ctype.lower():
        raise DownloadError(f"got HTML instead of CSV for {start}..{end} ({ctype})")
    _check_range(r.content, start, end, tz)
    return r.content


def _check_range(data: bytes, start: date, end: date, tz: str) -> None:
    """Refuse to cache a file whose measures lie outside the requested range or timezone (the
    server silently falls back to its default range when the form state is not accepted)."""
    lines = data.decode("utf-8-sig").splitlines()
    if len(lines) < 2 or not lines[0].startswith("BEGINN_DATUM;"):
        raise DownloadError("unexpected CSV header")
    rows = [ln.split(";") for ln in lines[1:] if ln.strip()]
    days = {pd.to_datetime(r[0], format="%d.%m.%Y").date() for r in rows}
    zones = {r[2] for r in rows}
    # a measure may start on the day before the range (running into it): allow one day slack
    if min(days) < start - pd.Timedelta(days=1) or max(days) > end:
        raise DownloadError(f"server returned {min(days)}..{max(days)}, asked {start}..{end}")
    if tz == "UTC" and zones != {"UTC"}:
        raise DownloadError(f"server returned time zones {zones}, asked UTC")


def fetch_month(year: int, month: int, tz: str = "UTC", retries: int = 5,
                backoff: float = 2.0) -> Path:
    start = date(year, month, 1)
    end = (pd.Timestamp(start) + pd.offsets.MonthEnd(1)).date()
    dest = RAW / f"redispatch_{year}_{month:02d}_{tz.replace('(', '').replace(')', '')}.csv"
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    last: Exception | None = None
    for attempt in range(retries):
        try:
            with requests.Session() as s:
                s.headers["User-Agent"] = USER_AGENT
                data = _post_month(s, start, end, tz)
            dest.write_bytes(data)
            append_manifest(f"{PAGE} (POST Download CSV {start}..{end}, {tz})", dest,
                            source_note="vault/data/netztransparenz Redispatch.md",
                            license="see vault note (no licence stated on page, 2026-11-05)",
                            notes="TSO redispatch measures, per measure and day")
            return dest
        except (requests.RequestException, DownloadError) as exc:
            last = exc
            time.sleep(backoff**attempt)
    raise DownloadError(f"failed after {retries} attempts: {start}..{end}: {last}")


def fetch_year(year: int = 2024, tz: str = "UTC") -> list[Path]:
    return [fetch_month(year, m, tz) for m in range(1, 13)]


if __name__ == "__main__":
    for p in fetch_year(2024):
        print(p, p.stat().st_size)
