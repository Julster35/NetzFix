"""A34 helpers: Imax precedence and substation-name normalisation (hand-checked cases)."""

import numpy as np
import pandas as pd

from netzfix.network.jao_ratings import _norm, imax


def test_imax_precedence():
    nan = np.nan
    d = pd.DataFrame({
        "fixed": [2000, nan, nan, nan],
        "dlrmin": [1500, 1535, nan, nan],
        "p1": [nan, nan, 1300, nan], "p2": [nan, nan, 1100, nan], "p3": [nan] * 4,
        "p4": [nan] * 4, "p5": [nan] * 4, "p6": [nan] * 4,
        "dlrmax": [nan, 1916, nan, 2000],
    })
    out = imax(d).tolist()
    assert out[:3] == [2000, 1535, 1100]       # fixed > DLRmin > lowest period
    assert np.isnan(out[3])                     # DLRmax alone is not used


def test_norm_strips_prefixes_and_umlauts():
    assert _norm("Umspannwerk Altlußheim") == "altlussheim"
    assert _norm("UW Daxlanden 220 kV") == "daxlanden"
    assert _norm("Karlsruhe-West") == "karlsruhe west"
