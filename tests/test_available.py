"""A28: available output never below actual; energy target met (hand-computed)."""

import numpy as np
import pytest

from netzfix.data.weather_profiles import available_target


def test_available_target_hand_computed():
    # actual [1, 1], raw [1, 3], energy 5: k*raw exceeds actual in both hours only if k >= 1;
    # then k + 3k = 5 -> k = 1.25, available [1.25, 3.75]
    k, av = available_target(np.array([1.0, 1.0]), np.array([1.0, 3.0]), 5.0)
    assert k == pytest.approx(1.25, abs=1e-9)
    assert np.allclose(av, [1.25, 3.75])


def test_available_never_below_actual():
    # energy 3: with k <= 1 hour 1 stays at actual 1 and 1 + 3k = 3 -> k = 2/3 (< 1, consistent)
    k, av = available_target(np.array([1.0, 1.0]), np.array([1.0, 3.0]), 3.0)
    assert k == pytest.approx(2 / 3, abs=1e-9)
    assert np.allclose(av, [1.0, 2.0])
