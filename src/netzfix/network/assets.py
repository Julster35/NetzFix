"""Baseline 2024 assets: MaStR producers/storage + regional consumers, attached to grid buses.

Rules (vault/project/Assumptions.md A19-A20):
- Time-varying fleet: a unit counts in month m of 2024 if it is operating at that month's end
  (commissioned, not finally decommissioned, not in a temporary shutdown). Each asset carries
  `p_nom_monthly` (12 values, MW); `p_nom` is the maximum over the year.
- Units >= UNIT_THRESHOLD_MW (at their maximum) are individual assets; smaller units are
  aggregated per bus x carrier.
- Location: own coordinates > powerplantmatching coordinates (matched by MaStR number) >
  municipality (Gemeindeschluessel -> GISCO LAU point) > district centre. `loc_source` records it.
- Carriers follow SMARD's categories so each unit follows its technology's national 2024 profile.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from netzfix.config import DATA_PROCESSED
from netzfix.data.regions import lau_points
from netzfix.network import demand, grid
from netzfix.network.attach import nearest_bus

UNIT_THRESHOLD_MW = 10.0
YEAR = 2024
MONTH_ENDS = pd.date_range(f"{YEAR}-01-31", periods=12, freq="ME")
MASTR_FILE = DATA_PROCESSED / "mastr_units_20261103.parquet"
OUT = DATA_PROCESSED / f"assets_baseline_{YEAR}.parquet"
REPORT = DATA_PROCESSED / f"assets_baseline_{YEAR}_report.json"
STORAGE = ("pumped_hydro", "battery", "other_storage")

COMBUSTION = {  # Energietraeger of EinheitenVerbrennung -> SMARD carrier; rest: other_conventional
    "Braunkohle": "lignite", "Steinkohle": "hard_coal", "Erdgas": "gas",
}
GSGK = {  # EinheitenGeothermieGrubengasDruckentspannung; values seen in the 2026-11-03 export
    "Geothermie": "other_renewable", "Klärschlamm": "other_renewable",
    "Druck aus Gasleitungen": "other_renewable", "Druck aus Wasserleitungen": "other_renewable",
    "Solarthermie": "other_renewable", "Grubengas": "other_conventional",
}


def carrier_of(u: pd.DataFrame) -> pd.Series:
    t = u["table"].astype(str)
    et = u["Energietraeger"].astype(str)
    c = pd.Series("unknown", index=u.index, dtype="object")
    c[t == "EinheitenSolar"] = "solar"
    wind = t == "EinheitenWind"
    sea = u["WindAnLandOderAufSee"].astype(str).str.contains("See", na=False)
    c[wind & ~sea] = "wind_onshore"
    c[wind & sea] = "wind_offshore"
    c[t == "EinheitenBiomasse"] = "biomass"
    c[t == "EinheitenWasser"] = "hydro"
    c[t == "EinheitenKernkraft"] = "nuclear"
    comb = t == "EinheitenVerbrennung"
    c[comb] = et[comb].map(COMBUSTION).fillna("other_conventional")
    g = t == "EinheitenGeothermieGrubengasDruckentspannung"
    c[g] = et[g].map(GSGK).fillna("other_renewable")
    st = t == "EinheitenStromSpeicher"
    tech = u["Technologie"].astype(str)
    c[st] = "other_storage"   # hydrogen, compressed air, flywheel, unknown
    c[st & tech.str.contains("Pumpspeicher", na=False)] = "pumped_hydro"
    c[st & tech.str.contains("Batterie", na=False)] = "battery"
    return c


def operating(u: pd.DataFrame, at: pd.Timestamp) -> pd.Series:
    on = u.Inbetriebnahmedatum.notna() & (u.Inbetriebnahmedatum <= at)
    gone = u.DatumEndgueltigeStilllegung.notna() & (u.DatumEndgueltigeStilllegung <= at)
    paused = (u.DatumBeginnVoruebergehendeStilllegung.notna()
              & (u.DatumBeginnVoruebergehendeStilllegung <= at)
              & (u.DatumWiederaufnahmeBetrieb.isna() | (u.DatumWiederaufnahmeBetrieb > at)))
    return on & ~gone & ~paused


def locate(u: pd.DataFrame) -> pd.DataFrame:
    """Priority: own coordinates > powerplantmatching (MaStR number) > municipality > district."""
    from netzfix.data.ppm import mastr_coordinates

    ppm = mastr_coordinates()
    see = u.EinheitMastrNummer.astype(str)
    p_lon, p_lat = see.map(ppm.lon), see.map(ppm.lat)
    own = u.Laengengrad.between(3.0, 15.5) & u.Breitengrad.between(45.5, 55.8)
    lon = u.Laengengrad.where(own, p_lon)
    lat = u.Breitengrad.where(own, p_lat)
    ok = lon.notna() & lat.notna()
    lau = lau_points()
    muni = lau.set_index("lau_id")
    # district (Kreis) = first 5 digits of the municipality key; centre = mean of its municipalities
    dist = lau.assign(kreis=lau.lau_id.str[:5]).groupby("kreis")[["lon", "lat"]].mean()
    ags = u.Gemeindeschluessel.astype("object").fillna("").astype(str)
    m_lon, m_lat = ags.map(muni.lon), ags.map(muni.lat)
    d_lon, d_lat = ags.str[:5].map(dist.lon), ags.str[:5].map(dist.lat)
    out = pd.DataFrame(index=u.index)
    out["lon"] = np.where(ok, lon, np.where(m_lon.notna(), m_lon, d_lon))
    out["lat"] = np.where(ok, lat, np.where(m_lat.notna(), m_lat, d_lat))
    out["loc_source"] = np.select(
        [own, ok, m_lon.notna(), d_lon.notna()],
        ["coordinates", "powerplantmatching", "municipality", "district"], "none")
    return out


def behaviour(carrier: str) -> str:
    if carrier == "pumped_hydro":
        return json.dumps({"type": "replay_pumped_hydro"})
    if carrier in ("battery", "other_storage"):
        return json.dumps({"type": "constant", "p_mw": 0,
                           "note": "no 2024 operation data; idle in baseline"})
    return json.dumps({"type": "national_profile", "carrier": carrier})


def build() -> Path:
    g = grid.load()
    buses = g.network.buses[g.network.buses.country == "DE"]  # not the NB-* neighbours
    u = pd.read_parquet(MASTR_FILE)
    report: dict = {"mastr_rows": len(u)}
    active = np.column_stack([operating(u, m).to_numpy() for m in MONTH_ENDS])  # units x 12
    keep = active.any(axis=1)
    u, active = u[keep].copy(), active[keep]
    report["operating_any_month_2024"] = len(u)
    u["carrier"] = carrier_of(u)
    u["p"] = (u.Nettonennleistung.fillna(u.Bruttoleistung) / 1000.0).astype(float)  # kW -> MW
    pos = (u.p > 0) & (u.carrier != "nuclear")
    report["dropped_nuclear_mw"] = round(float(u.loc[u.carrier == "nuclear", "p"].sum()), 1)
    u, active = u[pos].copy(), active[pos.to_numpy()]
    u = u.join(locate(u))
    report["location_source_units"] = u.loc_source.value_counts().to_dict()
    report["capacity_mw_by_location_source"] = u.groupby("loc_source").p.sum().round(1).to_dict()
    has = (u.loc_source != "none").to_numpy()
    report["dropped_no_location"] = u.loc[~has].groupby("carrier").p.sum().round(1).to_dict()
    u, active = u[has].copy(), active[has]
    u["bus"], u["dist_km"] = nearest_bus(buses, u.lon, u.lat)
    # Offshore wind lands at extra-high-voltage substations: attach to the nearest >= 380 kV bus
    # (A19b). Otherwise farms pile onto small 220 kV coastal stubs (seen 2026-11-03: 4.9 GW on
    # two stub buses near Emden, 4x overloads).
    off = (u.carrier == "wind_offshore").to_numpy()
    ehv = buses[buses.v_nom >= 380]
    u.loc[off, "bus"], u.loc[off, "dist_km"] = nearest_bus(ehv, u.lon[off], u.lat[off])
    report["median_dist_km"] = round(float(u.dist_km.median()), 1)

    monthly = active * u.p.to_numpy()[:, None]                               # MW per month-end
    mcols = [f"m{k:02d}" for k in range(1, 13)]
    u[mcols] = monthly
    report["capacity_mw_jan_dec_by_carrier"] = {
        c: [round(float(v), 1) for v in grp[["m01", "m12"]].sum()]
        for c, grp in u.groupby("carrier")}
    u["kind"] = np.where(u.carrier.isin(STORAGE), "storage", "producer")
    big = u.p >= UNIT_THRESHOLD_MW

    rows = [{
        "id": f"mastr/{r.EinheitMastrNummer}",
        "name": r.NameStromerzeugungseinheit or r.NameKraftwerk or f"{r.carrier} unit",
        "kind": r.kind, "carrier": r.carrier, "bus": r.bus, "p_nom": round(r.p, 3),
        "p_nom_monthly": [round(float(getattr(r, m)), 3) for m in mcols],
        "lon": r.lon, "lat": r.lat, "group": "unit", "n_units": 1,
        "behaviour": behaviour(r.carrier), "source": "mastr", "loc_source": r.loc_source,
    } for r in u[big].itertuples()]
    small = u[~big]
    agg = small.assign(wlon=small.lon * small.p, wlat=small.lat * small.p).groupby(
        ["bus", "carrier", "kind"], observed=True).agg(
        n_units=("p", "size"), wlon=("wlon", "sum"), wlat=("wlat", "sum"), p=("p", "sum"),
        **{m: (m, "sum") for m in mcols}).reset_index()
    rows += [{
        "id": f"agg/{r.bus}/{r.carrier}", "name": f"{r.carrier} – {r.n_units:,} small units",
        "kind": r.kind, "carrier": r.carrier, "bus": r.bus,
        "p_nom": round(max(getattr(r, m) for m in mcols), 3),
        "p_nom_monthly": [round(float(getattr(r, m)), 3) for m in mcols],
        "lon": r.wlon / r.p, "lat": r.wlat / r.p, "group": "aggregate",
        "n_units": int(r.n_units), "behaviour": behaviour(r.carrier), "source": "mastr",
        "loc_source": "mixed",
    } for r in agg.itertuples()]

    shares = demand.build(buses)
    rows += [{
        "id": f"load/{r.bus}", "name": f"demand {r.bus}", "kind": "consumer", "carrier": "load",
        "bus": r.bus, "p_nom": None, "p_nom_monthly": None,
        "lon": buses.at[r.bus, "x"], "lat": buses.at[r.bus, "y"],
        "group": "aggregate", "n_units": None,
        "behaviour": json.dumps({"type": "demand_share", "share": r.share}), "source": "lau_pop",
        "loc_source": "municipality",
    } for r in shares[shares.share > 0].itertuples()]

    assets = pd.DataFrame(rows)
    assets.to_parquet(OUT)
    counts = assets.groupby(["kind", "group"]).size().astype(int)
    report["assets"] = {f"{k[0]}/{k[1]}": int(v) for k, v in counts.items()}
    REPORT.write_text(json.dumps(report, indent=1, default=str), encoding="utf-8")
    return OUT


if __name__ == "__main__":
    print(build())
    print(REPORT.read_text(encoding="utf-8"))
