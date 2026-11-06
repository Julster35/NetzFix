"""A36: BNetzA element names -> config entries (no network or data files needed)."""

from netzfix.network.element_match import _skey, element_of_name, key, load_elements


def test_key_ignores_umlauts_and_replacement_char():
    assert key("D�rpen (D�rpen-Niederlangen)") == key("Dörpen (Dörpen-Niederlangen)")
    assert key("Gro�krotzenburg") == key("Großkrotzenburg")


def test_published_names_are_unique_and_resolve():
    els = load_elements()
    names = [n for e in els.values() for n in e["names"]]
    assert len({key(n) for n in names}) == len(names)
    m = element_of_name()
    assert m[key("Vierraden - Krajnik (DE_PL)")] == m[key("Vierraden - Krajnik (PL)")]


def test_chains_are_pairs_or_border_legs():
    for eid, e in load_elements().items():
        for chain in e["chains"]:
            assert len(chain) >= 2, eid
            assert all(isinstance(s, str) and s for s in chain), eid
            assert not chain[0].startswith("@"), eid


def test_substation_key_handles_polish_l_and_sankt():
    assert _skey("Mikułowa") == _skey("Mikulowa")
    assert _skey("Sankt Peter") == _skey("St. Peter")
