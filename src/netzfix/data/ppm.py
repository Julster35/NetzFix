"""powerplantmatching (PyPSA) plant coordinates, matched to MaStR unit numbers.

The public MaStR export has no coordinates for most large conventional plants (only a district
key). powerplantmatching's merged dataset (v0.9.1, CC-BY-4.0, `powerplants.csv`) carries lat/lon per
plant and lists the MaStR unit numbers it matched in `projectID` ('MASTR-SEE...').
"""

from __future__ import annotations

import re

import pandas as pd

from netzfix.config import DATA_RAW
from netzfix.data.download import fetch

VERSION = "v0.9.1"
URL = f"https://raw.githubusercontent.com/PyPSA/powerplantmatching/{VERSION}/powerplants.csv"
SEE = re.compile(r"MASTR-(SEE\d+)")


def mastr_coordinates() -> pd.DataFrame:
    """DataFrame indexed by MaStR unit number with columns lat, lon, ppm_name."""
    path = fetch(URL, DATA_RAW / "ppm" / f"powerplants_{VERSION}.csv",
                 source_note="vault/data/Marktstammdatenregister.md", license="CC-BY-4.0",
                 notes=f"powerplantmatching {VERSION} merged dataset (coordinates for MaStR units)")
    df = pd.read_csv(path, usecols=["Name", "lat", "lon", "projectID"])
    rows = [(see, r.lat, r.lon, r.Name)
            for r in df.dropna(subset=["lat", "lon"]).itertuples()
            for see in SEE.findall(str(r.projectID))]
    out = pd.DataFrame(rows, columns=["see", "lat", "lon", "ppm_name"])
    return out.drop_duplicates("see").set_index("see")
