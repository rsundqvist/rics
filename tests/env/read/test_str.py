import pytest

from rics.env.read import read_str

VAR = "MY_STR"


def test_blank_parts(monkeypatch):
    monkeypatch.setenv(VAR, ",  , , ")  # From the docstring
    assert read_str(VAR, split=",") == []


def test_parts_are_stripped(monkeypatch):
    monkeypatch.setenv(VAR, ", aa , b, ")
    assert read_str(VAR, split=",") == ["aa", "b"]


class TestDefaultOnly:
    @pytest.mark.parametrize("value", ["   ", "", None])
    def test_unset(self, monkeypatch, value):
        if value is None:
            monkeypatch.delenv(VAR, raising=False)
        else:
            monkeypatch.setenv(VAR, value)
        assert read_str(VAR, default="some-default") == "some-default"
