import logging
from datetime import datetime

import polars as pl
import pytest
from rics.ml.time_split import split
from rics.ml.time_split.integration.polars import split_polars


@pytest.fixture
def df():
    ts = pl.datetime_range(
        datetime.fromisoformat("2022-01-01"),
        datetime.fromisoformat("2022-01-10"),
        interval="1h",
        eager=True,
    )
    return pl.DataFrame({"timestamp": ts, "ints": range(len(ts))})


def test_polars(df, caplog):
    for expected_means, polars_fold, expected_bounds in zip(
        # From the docstring example
        [(83.5, 179.5), (107.5, 203.5)],
        split_polars(
            df,
            schedule="1d",
            log_progress={"logger": "test-polars", "start_level": logging.DEBUG},
            time_column="timestamp",
        ),
        split("1d", available=list(df["timestamp"])),
    ):
        assert isinstance(expected_bounds, type(polars_fold.bounds)), "bad"
        assert expected_bounds == polars_fold.bounds

        actual_means = polars_fold.data["ints"].mean(), polars_fold.future_data["ints"].mean()

        assert actual_means == expected_means

        record = caplog.records[-1]
        assert record.mid == polars_fold.bounds.mid.isoformat()
        assert record.message.startswith("Begin fold")
        assert record.levelno == logging.DEBUG
        assert record.name == "test-polars"


def test_bad_time(df):
    with pytest.raises(TypeError, match="'ints'"):
        list(split_polars(df, schedule="1d", time_column="ints", log_progress=False))
