"""Cached, retrying downloads that record every file in data/MANIFEST.csv.

Rule (vault/_CLAUDE.md, Section 0.5): never fabricate data. A failed download raises; callers must
not fall back to invented values.
"""

from __future__ import annotations

import csv
import hashlib
import time
from datetime import date
from pathlib import Path

import requests

from netzfix.config import MANIFEST, REPO_ROOT

USER_AGENT = "NetzFix research model (open-source; github.com/Julster35)"


class DownloadError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def append_manifest(url: str, path: Path, source_note: str, license: str, notes: str = "") -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    new = not MANIFEST.exists()
    with open(MANIFEST, "a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["url", "access_date", "sha256", "local_path", "source_note", "license",
                        "notes"])
        w.writerow([url, date.today().isoformat(), sha256(path),
                    path.resolve().relative_to(REPO_ROOT).as_posix(), source_note, license, notes])


def fetch(
    url: str,
    dest: Path,
    *,
    source_note: str,
    license: str,
    notes: str = "",
    md5: str | None = None,
    retries: int = 5,
    backoff: float = 2.0,
    manifest: bool = True,
) -> Path:
    """Download ``url`` to ``dest`` unless it already exists. Returns ``dest``.

    Retries with exponential backoff; verifies ``md5`` if given (Zenodo publishes md5).
    """
    dest = Path(dest)
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    last: Exception | None = None
    for attempt in range(retries):
        try:
            with requests.get(url, stream=True, timeout=60,
                              headers={"User-Agent": USER_AGENT}) as r:
                r.raise_for_status()
                with open(tmp, "wb") as fh:
                    for chunk in r.iter_content(1 << 20):
                        fh.write(chunk)
            if md5:
                h = hashlib.md5()
                with open(tmp, "rb") as fh:
                    for chunk in iter(lambda: fh.read(1 << 20), b""):
                        h.update(chunk)
                if h.hexdigest() != md5:
                    raise DownloadError(f"md5 mismatch for {url}")
            tmp.replace(dest)
            if manifest:
                append_manifest(url, dest, source_note, license, notes)
            return dest
        except (requests.RequestException, DownloadError) as exc:
            last = exc
            time.sleep(backoff**attempt)
    raise DownloadError(f"failed after {retries} attempts: {url}: {last}")
