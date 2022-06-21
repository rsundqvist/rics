import pytest

from rics.utility.collections import InheritedKeysDict


@pytest.fixture
def d():
    return InheritedKeysDict(
        default={0: "shared0", 1: "shared1"},
        specific={
            "ctx0": {0: "c0-v0"},
            "ctx1": {0: "c1-v0", 1: "c1-v1"},
        },
    )


def test_inherited_keys_dict(d):
    assert d["ctx0"] == {0: "c0-v0", 1: "shared1"}
    assert d["ctx1"] == {0: "c1-v0", 1: "c1-v1"}
    assert d["not-in-d"] == {0: "shared0", 1: "shared1"}
    assert len(d) == 2
    assert list(d) == ["ctx0", "ctx1"]


def test_copy(d):
    assert d == d.copy()
