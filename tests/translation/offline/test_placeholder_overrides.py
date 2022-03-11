import pytest

from rics.translation.offline import PlaceholderOverrides


@pytest.fixture(scope="module")
def overrides():
    return PlaceholderOverrides.from_dict(
        {
            "shared": {"mapped-from": "mapped-to"},
            "source-specific": {"special": {"special-mapped-from": "special-mapped-to"}},
        }
    )


@pytest.fixture(scope="module")
def reversed_overrides(overrides):
    return overrides.reverse()


def test_bad_keys():
    with pytest.raises(ValueError):
        PlaceholderOverrides.from_dict({"shared": {}, "source-specific": {}, "mystery-key": 0})


@pytest.mark.parametrize(
    "source,placeholder,expected",
    [
        ("not-special", "unmapped", "unmapped"),
        ("not-special", "mapped-from", "mapped-to"),
        ("special", "unmapped", "unmapped"),
        ("special", "special-mapped-from", "special-mapped-to"),
    ],
)
def test_overrides(overrides, source, placeholder, expected):
    assert PlaceholderOverrides.get_mapped_value(placeholder, overrides[source]) == expected


@pytest.mark.parametrize(
    "source,placeholder,expected",
    [
        ("not-special", "unmapped", "unmapped"),
        ("not-special", "mapped-to", "mapped-from"),
        ("not-special", "mapped-from", "mapped-from"),
        ("not-special", "special-mapped-to", "special-mapped-to"),
        ("special", "unmapped", "unmapped"),
        ("special", "special-mapped-to", "special-mapped-from"),
    ],
)
def test_reversed_overrides(reversed_overrides, source, placeholder, expected):
    assert PlaceholderOverrides.get_mapped_value(placeholder, reversed_overrides[source]) == expected
