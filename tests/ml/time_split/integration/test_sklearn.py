import logging

import pandas as pd
import pytest

from rics.ml.time_split.integration.pandas import split_pandas
from rics.ml.time_split.integration.sklearn import ScikitLearnSplitter


def test_sklearn(caplog):
    # Check against pandas implementation
    splitter = ScikitLearnSplitter("1d", log_progress={"logger": "test-sklearn", "start_level": logging.DEBUG})

    index = pd.date_range("2022", "2022-1-10", freq="h")
    array = index.array

    assert splitter.get_n_splits(array) == 2

    pandas_split = split_pandas(index.to_series(), "1d", log_progress=False)
    for (train_index, test_index), pandas_fold in zip(splitter.split(array), pandas_split):
        assert (pandas_fold.data.index == array[train_index]).all()
        assert (pandas_fold.future_data.index == array[test_index]).all()

        record = caplog.records[-1]
        assert pd.Timestamp(record.mid) == pandas_fold.bounds.mid
        assert record.message.startswith("Begin fold")
        assert record.levelno == logging.DEBUG
        assert record.name == "test-sklearn"


def test_bad_args():
    splitter = ScikitLearnSplitter("1d", flex=False)
    array = pd.date_range("2022", "2022-1-10", freq="h").array

    with pytest.raises(ValueError, match="are not equal."):
        splitter.get_n_splits(array, array[5:])

    with pytest.raises(ValueError, match="At least one of"):
        splitter.get_n_splits()


def test_cv():
    from sklearn.linear_model import LinearRegression  # type: ignore[import]
    from sklearn.model_selection import cross_val_score  # type: ignore[import]

    df = pd.DataFrame(index=pd.date_range("2022", "2022-1-10", freq="h"))
    df["x"] = range(len(df))
    df["y"] = df["x"] - 10
    df["z"] = df["x"] ** 2 - df["y"]

    res = cross_val_score(
        LinearRegression(),
        X=df[["x", "y"]],
        y=df["z"],
        cv=ScikitLearnSplitter("1d"),
    )
    assert len(res) == 2
