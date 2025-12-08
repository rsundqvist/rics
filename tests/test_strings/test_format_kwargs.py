import numpy as np
import pandas as pd
import pytest

from rics.strings import format_kwargs


@pytest.mark.parametrize(
    "value, expected",
    [
        (1, "1"),
        (1000, "1_000"),
        (None, "None"),
        (True, "True"),
        ("foo", "'foo'"),
        ("foo's bar", '"foo\'s bar"'),
        ("very-big-string" * 10, "str[150]"),
    ],
)
def test_simple_scalar(value, expected):
    actual = format_kwargs(dict(value=value))
    assert actual == f"value={expected}"


def test_collection():
    kwargs = {
        "dict": {"k": 1},
        "short_list": [1],
        "long_list": list(range(100)),
        "long_dict": {i: 0 for i in range(100)},
    }
    actual = format_kwargs(kwargs)
    assert actual == "dict={'k': 1}, short_list=[1], long_list=list[100], long_dict=dict[100]"


@pytest.mark.parametrize("include_module", [True, False])
def test_ndim_array(include_module):
    expected = "df=pd.DataFrame[2x3], array2d=np.ndarray[2x3], array3d=np.ndarray[5x2x3]"
    if not include_module:
        expected = expected.replace("pd.", "").replace("np.", "").replace("pl.", "")

    data = [[1, 2, 3], [1, 2, 3]]
    kwargs = {
        "df": pd.DataFrame(data),
        "array2d": np.array(data),
        "array3d": np.array([data] * 5),
    }
    actual = format_kwargs(kwargs, include_module=include_module)
    assert actual == expected
