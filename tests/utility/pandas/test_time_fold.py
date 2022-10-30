from itertools import product

import pandas as pd
import pytest
from matplotlib import pyplot as plt

from rics.utility.pandas import TimeFold

TEST_DATA = (
    [
        (
            dict(schedule="68h", after="1d"),
            [
                ("2022-01-06 16:00:00", range(8, 68), range(68, 80)),
                ("2022-01-09 12:00:00", range(42, 102), range(102, 114)),
                ("2022-01-12 08:00:00", range(76, 136), range(136, 148)),
            ],
        ),
        (
            dict(schedule="3d", before=1, after=1),
            [
                ("2022-01-04", range(0, 36), range(36, 72)),
                ("2022-01-07", range(36, 72), range(72, 108)),
                ("2022-01-10", range(72, 108), range(108, 144)),
            ],
        ),
        (
            dict(
                schedule=["2022-01-01", "2022-01-04", "2022-01-07", "2022-01-10", "2022-01-13", "2100"],
                before=1,
                after=1,
            ),
            [
                ("2022-01-04", range(0, 36), range(36, 72)),
                ("2022-01-07", range(36, 72), range(72, 108)),
                ("2022-01-10", range(72, 108), range(108, 144)),
            ],
        ),
        (
            dict(
                schedule=pd.DatetimeIndex(["2022-01-01", "2022-01-04", "2022-01-07", "2022-01-10", "2022-01-13"]),
                before=1,
                after=1,
            ),
            [
                ("2022-01-04", range(0, 36), range(36, 72)),
                ("2022-01-07", range(36, 72), range(72, 108)),
                ("2022-01-10", range(72, 108), range(108, 144)),
            ],
        ),
        (
            dict(schedule="3d", before="all", after=1),
            [
                ("2022-01-04", range(0, 36), range(36, 72)),
                ("2022-01-07", range(0, 72), range(72, 108)),
                ("2022-01-10", range(0, 108), range(108, 144)),
            ],
        ),
        (
            dict(schedule="0 0 * * MON,FRI", before="all", after=2),
            [
                ("2022-01-03", range(0, 24), range(24, 108)),
                ("2022-01-07", range(0, 72), range(72, 156)),
            ],
        ),
        (
            dict(schedule="3d", before=2, after="all"),
            [
                ("2022-01-7", range(0, 72), range(72, 168)),
                ("2022-01-10", range(36, 108), range(108, 168)),
                ("2022-01-13", range(72, 144), range(144, 168)),
            ],
        ),
        (
            dict(schedule="0 0 * * MON,FRI"),
            [
                ("2022-1-7", range(12, 72), range(72, 108)),
                ("2022-1-10", range(48, 108), range(108, 156)),
            ],
        ),
        (dict(before="100000d"), []),  # Should be empty
    ],
)


@pytest.mark.parametrize("use_index, to_str, kwargs_and_expected", product([False, True], [False, True], *TEST_DATA))
def test_iter(use_index, to_str, kwargs_and_expected):
    kwargs, expected = kwargs_and_expected

    df = pd.DataFrame(
        {
            "time": pd.date_range("2022", "2022-1-15", freq="2h"),
            "a regular ol' column": 1,
            "another one!": 123,
        }
    )

    if to_str:
        df["time"] = df.time.astype(str)

    if use_index:
        df = df.set_index("time")
        kwargs["time_column"] = None

    expected_dtypes = df.dtypes

    actual = list(TimeFold.iter(df, **kwargs))
    for (et, ed, efd), (t, d, fd) in zip(expected, actual):
        assert pd.Timestamp(et) == t, t
        assert expected_dtypes.equals(d.dtypes)
        assert expected_dtypes.equals(fd.dtypes)
        assert df.index[ed].equals(d.index), t
        assert df.index[efd].equals(fd.index), t
    assert len(actual) == len(expected)

    # Test plotting doesn't crash
    if expected:
        try:
            TimeFold.plot(df, **kwargs)
            TimeFold.plot(df, **kwargs, nrows=1, ncols=2)
            TimeFold.plot(df, **kwargs, nrows=1, ncols=2, tight_layout=False)
        finally:
            plt.close("all")
