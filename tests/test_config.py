"""Milestone 0 smoke tests: the package imports and the documented defaults load."""

from netzfix.config import REPO_ROOT, _deep_update, load_config


def test_defaults_match_assumptions_note():
    cfg = load_config()
    # These values are documented in vault/project/Assumptions.md; change both together.
    assert cfg["run"]["base_year"] == 2024
    assert cfg["run"]["weather_year"] == 2024
    assert cfg["network"]["s_max_pu"] == 0.7
    assert cfg["network"]["power_flow"] == "linear_dc"
    assert cfg["solver"]["name"] == "highs"


def test_deep_update_overrides_nested_keys_only():
    base = {"network": {"s_max_pu": 0.7, "n_clusters_de": 30}, "solver": {"name": "highs"}}
    out = _deep_update(base, {"network": {"s_max_pu": 0.6}})
    assert out["network"] == {"s_max_pu": 0.6, "n_clusters_de": 30}
    assert out["solver"] == {"name": "highs"}


def test_vault_entry_points_exist():
    for rel in ["vault/_CLAUDE.md", "vault/index.md", "vault/00_Home.md", "data/MANIFEST.csv"]:
        assert (REPO_ROOT / rel).exists(), rel
