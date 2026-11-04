"""Technology class and minimum load of individual thermal units (A30 mapping, A31).

Technology from MaStR `Technologie` and commissioning year:
- gas: "Gasturbinen mit nachgeschalteter Dampfturbine" -> gas_cc; other gas turbines and engines
  -> gas_gt; steam machines (Kondensations-/Gegendruckmaschine, Dampfmotor) -> gas_st;
- hard_coal: commissioned >= new_from_year -> hard_coal_super (minimum load "new"), else _sub;
- lignite: >= new_from_year -> lignite (new), else lignite (old).
Minimum loads come from `config` `unit_flex.min_load`; gas_st and other_conventional get none
(no value in the held source).
Output: data/processed/unit_technology_2024.csv (id, carrier, technology, year, min_load).
"""

from __future__ import annotations

import pandas as pd

from netzfix.config import DATA_PROCESSED, load_config

OUT = DATA_PROCESSED / "unit_technology_2024.csv"
RESERVE_OUT = DATA_PROCESSED / "grid_reserve_units.csv"
GT = ("Gasturbinen mit Abhitzekessel", "Gasturbinen ohne Abhitzekessel", "Verbrennungsmotor")


def classify(carrier: str, technologie: str | None, year: float | None, cfg: dict) -> tuple:
    """(technology, min_load key or None)."""
    new_from = cfg["unit_flex"]["new_from_year"]
    tech = str(technologie or "")
    if carrier == "gas":
        if tech == "Gasturbinen mit nachgeschalteter Dampfturbine":
            return "gas_cc", "gas_cc"
        if tech in GT:
            return "gas_gt", "gas_gt"
        return "gas_st", None
    if carrier == "hard_coal":
        new = year is not None and year == year and year >= new_from["hard_coal"]
        return ("hard_coal_super", "hard_coal_new") if new else ("hard_coal_sub", "hard_coal_old")
    if carrier == "lignite":
        new = year is not None and year == year and year >= new_from["lignite"]
        return "lignite", ("lignite_new" if new else "lignite_old")
    return carrier, None


def build(cfg: dict | None = None) -> pd.DataFrame:
    from netzfix.network.assets import MASTR_FILE

    cfg = cfg or load_config()
    a = pd.read_parquet(DATA_PROCESSED / "assets_baseline_2024.parquet",
                        columns=["id", "carrier", "group"])
    a = a[(a["group"] == "unit")
          & a["carrier"].isin(("lignite", "hard_coal", "gas", "other_conventional"))].copy()
    a["see"] = a["id"].str.replace("mastr/", "", regex=False)
    m = pd.read_parquet(MASTR_FILE, columns=["EinheitMastrNummer", "Technologie",
                                             "Inbetriebnahmedatum"])
    a = a.merge(m, left_on="see", right_on="EinheitMastrNummer", how="left")
    a["year"] = pd.to_datetime(a["Inbetriebnahmedatum"]).dt.year
    ml = cfg["unit_flex"]["min_load"]
    cls = [classify(r.carrier, r.Technologie, r.year, cfg) for r in a.itertuples()]
    a["technology"] = [c[0] for c in cls]
    a["min_load"] = [float(ml[c[1]]) if c[1] else 0.0 for c in cls]
    out = a[["id", "carrier", "technology", "year", "min_load"]]
    out.to_csv(OUT, index=False, encoding="utf-8")
    return out


def build_reserve(cfg: dict | None = None) -> pd.DataFrame:
    """A32: MaStR units whose BNetzA Kraftwerksliste status is a reserve / grid-security status."""
    from netzfix.config import DATA_RAW

    cfg = cfg or load_config()
    k = pd.read_csv(DATA_RAW / "bnetza" / "Kraftwerksliste_CSV.csv", sep=";", encoding="cp1252",
                    skiprows=9, dtype=str)
    st = set(cfg["grid_reserve"]["statuses"])
    r = k[k["Kraftwerksstatus"].isin(st)].copy()
    if r.empty:
        raise ValueError("no reserve statuses matched - check the status strings in config")
    r["mw"] = r["Nettonennleistung_MW"].str.replace(",", ".").astype(float)
    out = pd.DataFrame({"id": "mastr/" + r["EinheitMastrNummer"], "status": r["Kraftwerksstatus"],
                        "mw": r["mw"], "name": r["Anzeigename"]})
    out.to_csv(RESERVE_OUT, index=False, encoding="utf-8")
    return out


if __name__ == "__main__":
    rv = build_reserve()
    print("reserve units", len(rv), "MW", round(rv.mw.sum()))
    o = build()
    print(o.groupby(["carrier", "technology"]).agg(n=("id", "size"),
                                                   min_load=("min_load", "mean")).round(3))
