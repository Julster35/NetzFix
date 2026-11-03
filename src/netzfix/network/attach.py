"""Attach point locations (units, municipalities) to the nearest grid bus."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

LAT0 = 51.0  # projection centre for Germany


def _km(lon, lat) -> np.ndarray:
    lon, lat = np.asarray(lon, float), np.asarray(lat, float)
    return np.column_stack([lon * 111.32 * np.cos(np.radians(LAT0)), lat * 110.57])


def nearest_bus(buses: pd.DataFrame, lon, lat, prefer_voltage: float | None = None):
    """Return (bus ids, distance km) of the nearest bus for each point.

    buses: index = bus id, columns x (lon), y (lat), v_nom. If several buses share a site
    (220 and 380 kV in one substation), ties are broken towards `prefer_voltage` if given,
    else towards the lower voltage (closer to distribution).
    """
    b = buses
    if prefer_voltage is None:
        b = b.sort_values("v_nom")  # first hit on exact ties = lowest voltage
    else:
        b = b.assign(_d=(b.v_nom - prefer_voltage).abs()).sort_values("_d")
    tree = cKDTree(_km(b.x, b.y))
    d, i = tree.query(_km(lon, lat))
    return b.index.to_numpy()[i], d
