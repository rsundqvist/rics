import numpy as np
import pandas as pd
import pytest

from rics.translation.dio import resolve_io
from rics.translation.dio.exceptions import NotInplaceTranslatableError

from .conftest import TRANSLATED, UNTRANSLATED

NAME = "nconst"


@pytest.mark.parametrize("ttype", [list, tuple, pd.Index, pd.Series, np.array])
def test_sequence_insert(ttype, translation_map):
    actual, ans = _do_insert(translation_map, ttype, copy=True)
    _test_eq(ans, ttype(TRANSLATED[NAME]))
    _test_eq(actual, ttype(UNTRANSLATED[NAME]))


@pytest.mark.parametrize("ttype", [list, pd.Series])
def test_sequence_insert_inplace(ttype, translation_map):
    actual = ttype(UNTRANSLATED[NAME])
    translatable_io = resolve_io(actual)
    ans = translatable_io.insert(actual, [NAME], translation_map, copy=False)
    assert ans is None
    _test_eq(actual, ttype(TRANSLATED[NAME]))


def test_insert_inplace_array(translation_map):
    actual = np.array(UNTRANSLATED[NAME], dtype=object)
    translatable_io = resolve_io(actual)
    ans = translatable_io.insert(actual, [NAME], translation_map, copy=False)
    assert ans is None
    _test_eq(actual, np.array(TRANSLATED[NAME]))


def test_forbidden_insert_inplace(translation_map):
    actual = tuple(UNTRANSLATED[NAME])
    translatable_io = resolve_io(actual)

    with pytest.raises(NotInplaceTranslatableError):
        translatable_io.insert(actual, [NAME], translation_map, copy=False)


def _do_insert(translation_map, ttype, copy):
    actual = ttype(UNTRANSLATED[NAME])
    translatable_io = resolve_io(actual)
    ans = translatable_io.insert(actual, [NAME], translation_map, copy=copy)
    return actual, ans


def _test_eq(actual, expected):
    try:
        assert actual == expected
    except ValueError:
        assert all(actual == expected)
