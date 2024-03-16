import pandas as pd
import pytest
from rics.ml.time_split import split
from rics.ml.time_split import types as st

from .conftest import DATA_CASES, NO_DATA_CASES, NO_DATA_SCHEDULE, SPLIT_DATA


@pytest.mark.parametrize("kwargs, expected", *DATA_CASES)
def test_data(kwargs, expected):
    actual = split(**kwargs, available=SPLIT_DATA)

    for i, (left, right) in enumerate(zip(actual, expected)):
        assert left == st.DatetimeSplitBounds(*map(pd.Timestamp, right)), i
    assert len(actual) == len(expected)


class TestSnapToEnd:
    @staticmethod
    def _run(monkeypatch, *, snap_to_end):
        from rics.ml.time_split.settings import misc

        monkeypatch.setattr(misc, "snap_to_end", snap_to_end)

        dates = []
        for bounds in split(schedule="3d", before="3d", after="2d", available=SPLIT_DATA):
            for ts in bounds:
                assert ts.normalize() == ts
            dates.append(tuple(ts.date().isoformat() for ts in bounds))
        return dates

    def test_true(self, monkeypatch):
        actual = self._run(monkeypatch, snap_to_end=True)
        assert actual == [
            ("2022-01-03", "2022-01-06", "2022-01-08"),
            ("2022-01-06", "2022-01-09", "2022-01-11"),
            ("2022-01-09", "2022-01-12", "2022-01-14"),
        ]

    def test_false(self, monkeypatch):
        actual = self._run(monkeypatch, snap_to_end=False)
        assert actual == [
            ("2022-01-01", "2022-01-04", "2022-01-06"),
            ("2022-01-04", "2022-01-07", "2022-01-09"),
            ("2022-01-07", "2022-01-10", "2022-01-12"),
        ]


@pytest.mark.parametrize("kwargs, expected", *DATA_CASES)
def test_data_utc(kwargs, expected):
    actual = split(**kwargs, available=SPLIT_DATA.tz_localize("utc"))

    for i, (left, right) in enumerate(zip(actual, expected)):
        assert left == st.DatetimeSplitBounds(*(pd.Timestamp(ts, tz="utc") for ts in right)), i
    assert len(actual) == len(expected)


@pytest.mark.parametrize(
    "after, expected",
    NO_DATA_CASES,
)
def test_no_data(after, expected):
    actual = list(split(schedule=NO_DATA_SCHEDULE, before="5d", after=after))

    for i, (left, right) in enumerate(zip(actual, expected)):
        assert left == st.DatetimeSplitBounds(*map(pd.Timestamp, right)), i
    assert len(expected) == len(actual)


@pytest.mark.parametrize(
    "step, expected",
    [
        (
            1,
            [
                "2022-01-13",
                "2022-01-20",
                "2022-01-27",
                "2022-02-03",
                "2022-02-10",
                "2022-02-17",
                "2022-02-24",
            ],
        ),
        (2, ["2022-01-13", "2022-01-27", "2022-02-10", "2022-02-24"]),
        (3, ["2022-01-13", "2022-02-03", "2022-02-24"]),
        (4, ["2022-01-27", "2022-02-24"]),
        (7, ["2022-02-24"]),
        (8, ["2022-02-24"]),
    ],
)
class TestStep:
    @staticmethod
    def split(step, n_splits):
        return split(
            "0 0 * * THU",
            after="5d",
            available=pd.date_range("2022-01", "2022-03"),
            step=step,
            n_splits=n_splits,
        )

    def test_positive_and_negative(self, step, expected):
        assert [f.mid for f in self.split(step, n_splits=None)] == [pd.Timestamp(e) for e in expected]
        assert [f.mid for f in self.split(-step, n_splits=None)] == [pd.Timestamp(e) for e in reversed(expected)]

    @pytest.mark.parametrize("n_splits", [2, 3])
    def test_n_split(self, n_splits, step, expected):
        expected = expected[-n_splits:]
        assert [f.mid for f in self.split(step, n_splits=n_splits)] == [pd.Timestamp(e) for e in expected]
        assert [f.mid for f in self.split(-step, n_splits=n_splits)] == [pd.Timestamp(e) for e in reversed(expected)]
