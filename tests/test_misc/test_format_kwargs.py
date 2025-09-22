import pandas as pd
import polars as pl

from rics.misc import format_kwargs


def test_scalar():
    kwargs = {"a": 1, "b": True, "c": 1000}
    actual = format_kwargs(kwargs)
    assert actual == "a=1, b=True, c=1_000"


def test_collection():
    kwargs = {"dict": {"k": 1}, "short_list": [1], "long_list": list(range(100))}
    actual = format_kwargs(kwargs)
    assert actual == "dict={'k': 1}, short_list=[1], long_list=list[100]"


def test_ndim_array():
    data = {"a": [1, 2, 3], "b": [4, 5, 6]}
    kwargs = {"df_pandas": (pd.DataFrame(data)), "df_polars": (pl.DataFrame(data))}
    actual = format_kwargs(kwargs)
    assert actual == "df_pandas=DataFrame[3x2], df_polars=DataFrame[3x2]"
