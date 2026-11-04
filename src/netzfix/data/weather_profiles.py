"""Regional hourly capacity factors per grid bus from ERA5 (assumption A27).

Steps per carrier (wind_onshore, wind_offshore, solar):
1. atlite capacity-factor time series per ERA5 cell (turbine / panel from `config` `weather`).
2. Each MaStR unit (located as in `network.assets.located_units`, December-2024 capacity) is put
   in its nearest cutout cell; a bus's raw profile is the capacity-weighted mean over the cells
   of its units.
3. Hourly national scaling to SMARD: k(t) = SMARD_c(t) / sum_b cap_b(t) * cf_b(t), so the
   national total equals the measured one each hour (this also removes ERA5's level bias);
   regional shape comes from the weather. Values are clipped to [0, 1]; hours where the raw
   national sum is ~0 but SMARD is not fall back to the national capacity factor.
Output: data/processed/regional_cf_<carrier>_2024.parquet (index UTC hours, columns buses).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from netzfix.config import DATA_PROCESSED, load_config
from netzfix.data.era5 import cutout_path

CARRIERS = ("wind_onshore", "wind_offshore", "solar")
SMARD_FILE = DATA_PROCESSED / "smard_DE_2024.parquet"
REPORT = DATA_PROCESSED / "regional_cf_2024_report.json"


def out_path(carrier: str, year: int = 2024) -> Path:
    return DATA_PROCESSED / f"regional_cf_{carrier}_{year}.parquet"


def _cell_cf(cutout, carrier: str, w: dict):
    """(time, y, x) capacity factors."""
    if carrier == "solar":
        da = cutout.pv(panel=w["solar_panel"], orientation=w["solar_orientation"],
                       capacity_factor_timeseries=True)
    else:
        da = cutout.wind(turbine=w[f"{carrier}_turbine"], capacity_factor_timeseries=True)
    return da.transpose("time", "y", "x").values.astype("float32"), da


def build(year: int = 2024) -> dict:
    import atlite

    from netzfix.network.assets import MCOLS, located_units

    cfg = load_config()
    w = cfg["weather"]
    cutout = atlite.Cutout(cutout_path(cfg))
    xs, ys = cutout.coords["x"].values, cutout.coords["y"].values
    units, _, _ = located_units()
    smard = pd.read_parquet(SMARD_FILE)
    month = smard.index.tz_convert("Europe/Berlin").month.to_numpy() - 1
    report: dict = {"cutout": cutout_path(cfg).name}
    for carrier in CARRIERS:
        cf, da = _cell_cf(cutout, carrier, w)
        times = pd.DatetimeIndex(da["time"].values).tz_localize("UTC")
        u = units[units["carrier"] == carrier]
        ix = np.abs(u["lon"].to_numpy()[:, None] - xs[None, :]).argmin(axis=1)
        iy = np.abs(u["lat"].to_numpy()[:, None] - ys[None, :]).argmin(axis=1)
        cap = u["m12"].to_numpy()
        lay = (pd.DataFrame({"bus": u["bus"].to_numpy(), "iy": iy, "ix": ix, "cap": cap})
               .groupby(["bus", "iy", "ix"]).cap.sum().reset_index())
        lay = lay[lay.cap > 0]
        lay["w"] = lay.cap / lay.groupby("bus").cap.transform("sum")
        buses = sorted(lay.bus.unique())
        bpos = {b: i for i, b in enumerate(buses)}
        raw = np.zeros((cf.shape[0], len(buses)), dtype="float32")
        for r in lay.itertuples():
            raw[:, bpos[r.bus]] += r.w * cf[:, r.iy, r.ix]
        raw = pd.DataFrame(raw, index=times, columns=buses).reindex(smard.index)
        # first local hour of 2024 (2023-12-31 23:00 UTC) is outside the ERA5 2024 cutout
        raw = raw.bfill(limit=1)
        if raw.isna().any().any():
            raise ValueError(f"{carrier}: ERA5 profiles do not cover all SMARD hours")
        # bus capacity per month (all units of the carrier at that bus, same set as assets)
        capm = u.groupby("bus")[MCOLS].sum().reindex(buses).fillna(0.0).to_numpy()  # bus x 12
        cap_t = capm[:, month].T                                                  # T x bus
        nat_raw = (raw.to_numpy() * cap_t).sum(axis=1)
        target = smard[carrier].to_numpy(dtype="float64")
        with np.errstate(divide="ignore", invalid="ignore"):
            k = np.where(nat_raw > 1.0, target / nat_raw, np.nan)
            nat_cf = target / cap_t.sum(axis=1)
        scaled = raw.to_numpy() * np.nan_to_num(k)[:, None]
        fb = np.isnan(k) & (target > 1.0)
        scaled[fb] = nat_cf[fb, None]
        scaled = np.clip(scaled, 0.0, 1.0)
        out = pd.DataFrame(scaled.astype("float32"), index=smard.index, columns=buses)
        out.to_parquet(out_path(carrier, year))
        got = (scaled * cap_t).sum(axis=1)
        report[carrier] = {
            "units": int(len(u)), "buses": len(buses),
            "raw_era5_twh": float(nat_raw.sum() / 1e6), "smard_twh": float(target.sum() / 1e6),
            "scaled_twh": float(got.sum() / 1e6),
            "k_median": float(np.nanmedian(k)), "k_p95": float(np.nanpercentile(k, 95)),
            "fallback_hours": int(fb.sum()),
            "corr_raw_vs_smard": float(np.corrcoef(nat_raw, target)[0, 1]),
        }
    REPORT.write_text(json.dumps(report, indent=1), encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(build(), indent=1))
