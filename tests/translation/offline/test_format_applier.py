import pytest

from rics.translation.offline import TranslationMap
from rics.translation.offline.exceptions import MalformedPlaceholderError


def test_missing_id():
    with pytest.raises(KeyError):
        TranslationMap.FORMAT_APPLIER_TYPE("source", {"foo": ["1", "2", "3"]})


def test_missing_placeholder():
    with pytest.raises(ValueError):
        TranslationMap.FORMAT_APPLIER_TYPE("source", {"id": [1, 2], "baz": [1, 2]}, default={"bar": "default"})


def test_malformed():
    with pytest.raises(MalformedPlaceholderError):
        TranslationMap.FORMAT_APPLIER_TYPE("source", {"id": [1, 2], "baz": [1, 2, 3]})
