import pytest

from rics.env.read import read_bool

EXPLICIT = [
    # False values
    ("0", False),
    ("false", False),
    ("FALSE", False),
    ("False", False),
    ("no", False),
    ("disabled", False),
    ("off", False),
    # True values
    ("1", True),
    ("true", True),
    ("TRUE", True),
    ("True", True),
    ("yes", True),
    ("enabled", True),
    ("on", True),
]
VAR = "MY_BOOL"


@pytest.mark.parametrize("value, expected", [*EXPLICIT, ("junk", True), ("", True)])
def test_default_true(monkeypatch, value, expected):
    monkeypatch.setenv(VAR, value)

    actual = read_bool(VAR, default=True, strict=False)
    assert actual == expected


@pytest.mark.parametrize("value, expected", [*EXPLICIT, ("junk", False), ("", False)])
def test_default_false(monkeypatch, value, expected):
    monkeypatch.setenv(VAR, value)

    actual = read_bool(VAR, default=False, strict=False)
    assert actual == expected


@pytest.mark.parametrize("value, expected", [*EXPLICIT, ("junk", None), ("", False)])
def test_strict(monkeypatch, value, expected):
    monkeypatch.setenv(VAR, value)

    if expected is None:
        match = "Bad value MY_BOOL='junk'; not a valid `bool` value: Cannot cast 'junk' to `bool`."
        with pytest.raises(ValueError, match=match):
            read_bool(VAR, strict=True)
    else:
        actual = read_bool(VAR, strict=True)
        assert actual == expected


class TestList:
    def test_bad_item_strict_false(self, monkeypatch):
        monkeypatch.setenv(VAR, "true, not-a-bool")
        actual = read_bool(VAR, split=",", strict=False)
        assert actual == [False]

    def test_bad_item_strict_true(self, monkeypatch):
        monkeypatch.setenv(VAR, "true, not-a-bool")

        with pytest.raises(ValueError) as exc_info:
            read_bool(VAR, split=",")

        expected = (
            "Bad value MY_BOOL='true, not-a-bool'; not a valid `list[bool]` value."
            "\nNOTE: Failed at MY_BOOL[1]='not-a-bool': Cannot cast 'not-a-bool' to `bool`."
        )
        assert str(exc_info.value) == expected

    def test_list(self, monkeypatch):
        monkeypatch.setenv(VAR, "true, 0, false   , 1, yes, no, on,  off")
        actual = read_bool(VAR, split=",")
        assert actual == [True, False, False, True, True, False, True, False]
