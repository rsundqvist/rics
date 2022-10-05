import pandas as pd
import pytest

from rics.utility.pandas import TimeFold


@pytest.mark.parametrize(
    "kwargs, expected",
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
            dict(schedule="0 0 * * MON,FRI"),
            [
                ("2022-1-7", range(12, 72), range(72, 108)),
                ("2022-1-10", range(48, 108), range(108, 156)),
            ],
        ),
    ],
)
def test_iter(kwargs, expected):
    df = pd.DataFrame({"time": pd.date_range("2022", "2022-1-15", freq="2h")})

    assert len(list(TimeFold.iter(df, **kwargs))) == len(expected)
    for (et, ed, efd), (t, d, fd) in zip(expected, TimeFold.iter(df, **kwargs)):
        assert pd.Timestamp(et) == t, t
        assert pd.Index(ed).equals(d.index), t
        assert pd.Index(efd).equals(fd.index), t


def test_plot_doesnt_crash():
    df = pd.DataFrame({"time": pd.date_range("2022", "2022-2")})
    TimeFold.plot(df, schedule="0 0 * * MON,FRI")
