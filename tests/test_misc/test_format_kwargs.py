import pandas as pd
import numpy as np

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
    data = [
        [1, 2, 3],
        [1, 2, 3]
    ]
    kwargs = {"df": pd.DataFrame(data), "array2d": np.array(data), "array3d": np.array([data]*5)}
    actual = format_kwargs(kwargs)
    assert actual == "df=DataFrame[2x3], array2d=ndarray[2x3], array3d=ndarray[5x2x3]"


def test_ndim_array2():
    data = [
        [1, 2, 3],
        [1, 2, 3]
    ]
    kwargs = {"df": pd.DataFrame(data), "array2d": np.array(data), "array3d": np.array([data]*5)}
    actual = format_kwargs(kwargs, max_value_length=0)
    assert actual == "df=DataFrame[2x3], array2d=ndarray[2x3], array3d=ndarray[5x2x3]"
