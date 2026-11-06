"""Configuration loading and repository paths.

All model settings live in ``config/default.yaml``; scenario files in ``config/scenarios/``
override them key by key. Paths are built with ``pathlib`` so they work on Windows and WSL.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "config"
DATA_RAW = REPO_ROOT / "data" / "raw"
DATA_PROCESSED = REPO_ROOT / "data" / "processed"
MANIFEST = REPO_ROOT / "data" / "MANIFEST.csv"
RESULTS = REPO_ROOT / "results"
WEB_DATA = REPO_ROOT / "web" / "public" / "data"


def _deep_update(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_update(out[key], value)
        else:
            out[key] = value
    return out


def load_config(scenario: str | Path | None = None) -> dict[str, Any]:
    """Load the default config, optionally overridden by a scenario YAML file.

    Without an explicit `scenario`, the environment variable NETZFIX_SCENARIO (a file name in
    config/scenarios/ or a path) selects one, so batch jobs can run a variant without editing
    default.yaml.
    """
    if scenario is None:
        scenario = os.environ.get("NETZFIX_SCENARIO") or None
    with open(CONFIG_DIR / "default.yaml", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    if scenario is not None:
        path = Path(scenario)
        if not path.is_absolute():
            path = CONFIG_DIR / "scenarios" / path
        with open(path, encoding="utf-8") as fh:
            cfg = _deep_update(cfg, yaml.safe_load(fh) or {})
    return cfg
