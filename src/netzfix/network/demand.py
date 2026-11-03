"""Regionalise national demand onto grid buses (assumption A12, version 0: population only).

Each NUTS3 region's population is split over the Voronoi cells of the grid buses by area overlap
(population assumed uniform within a NUTS3 region). The resulting bus shares sum to 1 and multiply
the hourly national load. Industrial demand is NOT located separately in v0: the weakest layer.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import shapely
from shapely import wkt as shp_wkt
from shapely.geometry import MultiPoint, Point
from shapely.ops import unary_union

from netzfix.config import DATA_PROCESSED


def _to_km(lon: np.ndarray, lat: np.ndarray, lat0: float = 51.0) -> tuple[np.ndarray, np.ndarray]:
    """Equirectangular projection around Germany (good enough for Voronoi area shares)."""
    return lon * 111.32 * np.cos(np.radians(lat0)), lat * 110.57


def bus_shares(buses: pd.DataFrame, nuts3: pd.DataFrame) -> pd.DataFrame:
    """Return DataFrame [bus, share, population] with shares summing to 1.

    buses: index bus id, columns x (lon), y (lat). nuts3: columns nuts3, population, wkt.
    """
    bx, by = _to_km(buses.x.to_numpy(), buses.y.to_numpy())
    def proj(c):
        return np.column_stack(_to_km(c[:, 0], c[:, 1]))

    regions = [shapely.transform(shp_wkt.loads(w), proj)
               for w in nuts3.wkt]
    land = unary_union(regions)
    cells = shapely.voronoi_polygons(MultiPoint(list(zip(bx, by, strict=True))), extend_to=land)
    # map each Voronoi cell back to its generating bus
    pts = [Point(x, y) for x, y in zip(bx, by, strict=True)]
    tree = shapely.STRtree(pts)
    cell_bus = {}
    for cell in cells.geoms:
        idx = tree.query(cell, predicate="contains")
        if len(idx):
            cell_bus[int(idx[0])] = cell
    pop_bus = np.zeros(len(buses))
    ctree = shapely.STRtree(list(cell_bus.values()))
    keys = list(cell_bus.keys())
    for reg, pop in zip(regions, nuts3.population.to_numpy(), strict=True):
        hits = ctree.query(reg, predicate="intersects")
        areas = np.array([reg.intersection(list(cell_bus.values())[h]).area for h in hits])
        if areas.sum() <= 0:
            continue
        for h, a in zip(hits, areas, strict=True):
            pop_bus[keys[h]] += pop * a / areas.sum()
    out = pd.DataFrame({"bus": buses.index, "population": pop_bus})
    out["share"] = out.population / out.population.sum()
    return out


def build(network_buses: pd.DataFrame, pop_year: int = 2024) -> pd.DataFrame:
    """Default (A12 v0): municipal (LAU) population at each municipality's representative point,
    attached to the nearest bus. Finer than the NUTS3 area split in `bus_shares`, which is kept as
    an alternative for sensitivity checks."""
    from netzfix.data.regions import lau_points
    from netzfix.network.attach import nearest_bus

    lau = lau_points(pop_year)
    bus, _ = nearest_bus(network_buses, lau.lon, lau.lat)
    pop = lau.assign(bus=bus).groupby("bus").population.sum()
    out = pd.DataFrame({"bus": network_buses.index})
    out["population"] = out.bus.map(pop).fillna(0.0)
    out["share"] = out.population / out.population.sum()
    return out


def build_nuts3_area(network_buses: pd.DataFrame, pop_year: int = 2024) -> pd.DataFrame:
    nuts3 = pd.read_parquet(DATA_PROCESSED / f"nuts3_DE_pop{pop_year}.parquet")
    return bus_shares(network_buses[["x", "y"]], nuts3)
