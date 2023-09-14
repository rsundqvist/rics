import numpy as np
import pandas as pd
import pytest

from rics.ml.time_split import split
from rics.ml.time_split.support import fold_weight


def _split(typ, unit):
    available = typ(pd.date_range("2022", "2022-1-21", freq="38min"))

    schedule = "0 0 * * MON,FRI"
    splits = split(schedule, before="all", after="3d", available=available)

    return fold_weight(splits, unit=unit, available=available)


@pytest.mark.parametrize("typ", [list, np.array, pd.Series, pd.Index])
class TestUnitCount:
    def test_rows(self, typ):
        actual = _split(typ, "rows")
        assert actual == [
            (76, 114),
            (228, 114),
            (342, 113),
            (493, 114),
            (607, 113),
        ]

    def test_hours(self, typ):
        actual = _split(typ, "hours")
        assert actual == [
            (48, 72),
            (144, 72),
            (216, 72),
            (312, 72),
            (384, 72),
        ]


def test_rows_without_available():
    with pytest.raises(ValueError, match="provide available data"):
        fold_weight([], unit="rows", available=None)
