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
            dict(schedule="3d", before=1, after=1),
            [
                ("2022-01-04", range(0, 36), range(36, 72)),
                ("2022-01-07", range(36, 72), range(72, 108)),
                ("2022-01-10", range(72, 108), range(108, 144)),
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
def test_iter(kwargs, expected):
    df = pd.DataFrame({"time": pd.date_range("2022", "2022-1-15", freq="2h")})

    actual = list(TimeFold.iter(df, **kwargs))
    for (et, ed, efd), (t, d, fd) in zip(expected, actual):
        assert pd.Timestamp(et) == t, t
        assert pd.Index(ed).equals(d.index), t
        assert pd.Index(efd).equals(fd.index), t
    assert len(actual) == len(expected)

    # Test plotting doesn't crash
    if expected:
        TimeFold.plot(df, **kwargs)
