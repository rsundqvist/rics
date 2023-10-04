import pandas as pd
import pytest

from rics.ml.time_split import split, types as st

from .conftest import DATA_CASES, NO_DATA_CASES, NO_DATA_SCHEDULE, SPLIT_DATA


@pytest.mark.parametrize("kwargs, expected", *DATA_CASES)
def test_data(kwargs, expected):
    actual = split(**kwargs, available=SPLIT_DATA)

    for i, (left, right) in enumerate(zip(actual, expected)):
        right = st.DatetimeSplitBounds(*map(pd.Timestamp, right))
        assert left == right, i
    assert len(actual) == len(expected)


@pytest.mark.parametrize("kwargs, expected", *DATA_CASES)
def test_data_utc(kwargs, expected):
    actual = split(**kwargs, available=SPLIT_DATA.tz_localize("utc"))

    for i, (left, right) in enumerate(zip(actual, expected)):
        right = st.DatetimeSplitBounds(*(pd.Timestamp(ts, tz="utc") for ts in right))
        assert left == right, i
    assert len(actual) == len(expected)


@pytest.mark.parametrize(
    "after, expected",
    NO_DATA_CASES,
)
def test_no_data(after, expected):
    actual = list(split(schedule=NO_DATA_SCHEDULE, before="5d", after=after))

    for i, (left, right) in enumerate(zip(actual, expected)):
        right = st.DatetimeSplitBounds(*map(pd.Timestamp, right))
        assert left == right, i
    assert len(expected) == len(actual)
