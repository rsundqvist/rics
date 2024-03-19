import logging

import pandas as pd
import pytest
from rics.ml.time_split import split
from rics.ml.time_split._backend._available import process_available
from rics.ml.time_split.integration.pandas import split_pandas


@pytest.mark.parametrize("typ", [pd.Series, pd.DataFrame])
def test_pandas(typ, caplog):
    index = pd.date_range("2022", "2022-1-10", freq="h")

    for expected_means, pandas_fold, expected_bounds in zip(
        # From the docstring example
        [(83.5, 179.5), (107.5, 203.5)],
        split_pandas(
            typ(range(len(index)), index=index),
            schedule="1d",
            log_progress={"logger": "test-pandas", "start_level": logging.DEBUG},
        ),
        split("1d", available=index),
    ):
        assert isinstance(expected_bounds, type(pandas_fold.bounds)), "bad"
        assert expected_bounds == pandas_fold.bounds

        if typ is pd.DataFrame:
            actual_means = pandas_fold.data[0].mean(), pandas_fold.future_data[0].mean()
        else:
            actual_means = pandas_fold.data.mean(), pandas_fold.future_data.mean()

        assert actual_means == expected_means

        record = caplog.records[-1]
        assert pd.Timestamp(record.mid) == pandas_fold.bounds.mid
        assert record.message.startswith("Begin fold")
        assert record.levelno == logging.DEBUG
        assert record.name == "test-pandas"


def test_bad_time():
    df = pd.DataFrame({"not-time": [1, 2, 3, 4]})
    with pytest.raises(TypeError, match="'not-time'"):
        list(split_pandas(df, schedule="1d", time_column="not-time", log_progress=False))


def test_inclusive_equality():
    df = pd.date_range("1999-04-30", end="1999-04-30 00:00:00.0000005", freq="1 ns").to_frame(name="time")
    assert len(df) < 3000, "test suite performance may suffer"

    kwargs = dict(data=df, schedule="100ns", before="30 ns")
    by_index = split_pandas(**kwargs, time_column=None)
    by_column = split_pandas(**kwargs, time_column="time")

    count = 0
    for index, column in zip(by_index, by_column):
        assert index.bounds == column.bounds
        pd.testing.assert_frame_equal(index.data, column.data)
        pd.testing.assert_frame_equal(index.future_data, column.future_data)
        count += 1

    assert count == 4


def test_index_is_preserved():
    available = pd.date_range("2023-05-01", "2023-06-01", periods=100)

    actual = process_available(available, flex=False).available_as_index
    assert id(available) == id(actual)


def test_series_is_preserved():
    available = pd.date_range("2023-05-01", "2023-06-01", periods=100).to_series()

    actual = process_available(available, flex=False).available_as_index
    assert isinstance(actual, pd.Series)
