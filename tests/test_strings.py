import pytest

from rics import strings


def test_without_suffix():
    assert strings.without_suffix("foobarfoo", "foo") == "foobar"

    with pytest.raises(ValueError):
        strings.without_suffix("foobarfoo", "baz")


def test_without_prefix():
    assert strings.without_prefix("foobarfoo", "foo") == "barfoo"

    with pytest.raises(ValueError):
        strings.without_prefix("foobarfoo", "baz")
