import pytest

from rics.translation.offline import Format, TranslationMap
from rics.translation.offline.exceptions import MalformedPlaceholderError


@pytest.fixture(scope="module")
def fmt():
    return Format("{foo} {id}[: baz={baz}]")


def test_missing_id():
    with pytest.raises(KeyError):
        TranslationMap.FORMAT_APPLIER_TYPE("source", {"foo": ["1", "2", "3"]})


def test_missing_default_placeholder():
    with pytest.raises(ValueError):
        TranslationMap.FORMAT_APPLIER_TYPE("source", {"id": [1, 2], "baz": [1, 2]}, default={"bar": "default"})


def test_malformed():
    with pytest.raises(MalformedPlaceholderError):
        TranslationMap.FORMAT_APPLIER_TYPE("source", {"id": [1, 2], "baz": [1, 2, 3]})


def test_no_explicit_placeholders(fmt):
    applier = TranslationMap.FORMAT_APPLIER_TYPE("source", {"id": [1, 2], "baz": [1, 2], "foo": [3, 4]})

    ans = applier(fmt)
    assert ans == {1: "3 1: baz=1", 2: "4 2: baz=2"}


def test_explicit_placeholders(fmt):
    applier = TranslationMap.FORMAT_APPLIER_TYPE(
        "source", {"id": [1, 2], "baz": [1, 2], "foo": [3, 4]}, default={"baz": "default-baz", "foo": "default-baz"}
    )

    ans = applier(fmt, ("foo", "id"))
    assert ans == {1: "3 1", 2: "4 2"}
