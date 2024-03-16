import pandas as pd
import pytest
from rics.ml.time_split import split


def fold_from_mid(arg):
    mid = pd.Timestamp(arg)
    return mid - pd.Timedelta(days=5), mid, mid + pd.Timedelta(days=1)


@pytest.mark.parametrize(
    "flex, freq, expected",
    [
        ("h", "30 min", "06, 07, 08, 09"),
        ("d", "30 min", "06, 07, 08, 09"),
        ("min", "30 min", "07, 08"),
        # Asymmetrical flex - not implemented
        # (("d", "h"), "30 min", "06, 07, 08, 09"),
        # (("h", "d"), "30 min", "06, 07, 08, 09"),
    ],
)
def test_flex(flex, freq, expected):
    schedule = ["2022-01-06", "2022-01-07", "2022-01-08", "2022-01-09", "2022-01-10"]
    available = pd.date_range("2022-01-01 00:00:00", "2022-01-10 00:00:00", freq=freq, inclusive="neither")

    actual = split(schedule, before="5d", after="1d", flex=flex, available=available)
    assert actual == [fold_from_mid(f"2022-1-{e.strip()}") for e in expected.split(",")]
