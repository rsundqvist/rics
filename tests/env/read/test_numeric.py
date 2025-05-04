from math import isnan

import pytest

from rics.env.read import read_float, read_int


@pytest.mark.parametrize(
    "value, expected",
    [
        ("-1", -1),
        ("0", 0),
        ("", 0),
        ("1", 1),
    ],
)
def test_int(monkeypatch, value, expected):
    assert isinstance(expected, int)
    name = "MY_VAR"
    monkeypatch.setenv(name, value)

    actual = read_int(name, strict=False)
    assert isinstance(actual, int)
    assert actual == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        ("-1", -1.0),
        ("-1.0", -1.0),
        ("0", 0.0),
        ("00.000", 0.0),
        ("", 0.0),
        ("1", 1.0),
        ("1.23", 1.23),
    ],
)
def test_float(monkeypatch, value, expected):
    assert isinstance(expected, float)

    name = "MY_VAR"
    monkeypatch.setenv(name, value)

    actual = read_float(name, strict=False)
    assert isinstance(actual, float)
    assert actual == expected


def test_nan(monkeypatch):
    name = "MY_VAR"
    monkeypatch.setenv(name, "nan")

    actual = read_float(name, strict=False)
    assert isinstance(actual, float)
    assert isnan(actual)


@pytest.mark.parametrize("value", ["dsadasdas", "1.2", "nan"])
def test_strict_int(monkeypatch, value):
    name = "MY_VAR"
    monkeypatch.setenv(name, value)

    with pytest.raises(ValueError, match="not a valid `int` value"):
        read_int(name)


@pytest.mark.parametrize("value", ["dsadasdas", "false", "true"])
def test_strict_float(monkeypatch, value):
    name = "MY_VAR"
    monkeypatch.setenv(name, value)

    with pytest.raises(ValueError, match="not a valid `float` value"):
        read_float(name)
