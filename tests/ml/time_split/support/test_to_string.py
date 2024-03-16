from datetime import datetime

import pandas as pd
import pytest
from rics.ml.time_split.support import to_string
from rics.ml.time_split.types import DatetimeSplitBounds

TUPLES = [
    DatetimeSplitBounds(
        pd.Timestamp("1999-04-30"),
        pd.Timestamp("1991-06-05"),
        pd.Timestamp("2019-05-11 21:00"),
    ),
    ("1999-04-30", pd.Timestamp("1991-06-05"), datetime(2019, 5, 11, 21)),
]
IDS = [type(bounds).__name__ for bounds in TUPLES]


@pytest.mark.parametrize("bounds", TUPLES, ids=IDS)
def test_to_string_default(bounds):
    expected = "'1999-04-30' <= [schedule: '1991-06-05' (Wednesday)] < '2019-05-11 21:00:00'"
    assert to_string(bounds) == expected
    assert to_string(*bounds) == expected


@pytest.mark.parametrize("bounds", TUPLES, ids=IDS)
def test_to_string_setting(bounds, monkeypatch):
    from rics.ml.time_split.settings import log_split_progress

    monkeypatch.setattr(log_split_progress, "FOLD_FORMAT", "{end.auto}")
    expected = "2019-05-11 21:00:00"
    assert to_string(bounds) == expected
    assert to_string(*bounds) == expected


@pytest.mark.parametrize("bounds", TUPLES, ids=IDS)
def test_to_string_custom_bounds(bounds):
    custom = "{start} | {mid.auto} | {end}"
    expected = "1999-04-30 00:00:00 | 1991-06-05 | 2019-05-11 21:00:00"
    assert to_string(bounds, format=custom) == expected
    assert to_string(*bounds, format=custom) == expected


def test_bad_args():
    start, mid, end = "1999-04-30", "1991-06-05", "2019-05-11 21:00:00"

    with pytest.raises(TypeError, match="Too many"):
        to_string((start, mid, end), mid, end)  # TODO(richard): This should need an ignore, check mypy.ini
    with pytest.raises(TypeError, match="Too few"):
        to_string(start)  # type: ignore[call-overload]
    with pytest.raises(TypeError, match="Too few"):
        to_string(start, mid)  # type: ignore[call-overload]
