import pytest
from rics.collections.dicts import (
    DictComparer,
    InheritedKeysDict,
    compute_if_absent,
    flatten_dict,
    reverse_dict,
    unflatten_dict,
)


def test_compute_if_absent():
    d = {"bar": "real-bar"}

    with pytest.raises(KeyError):
        compute_if_absent(d, "foo")
    assert "foo" not in d

    assert compute_if_absent(d, "foo", "{}bar".format) == "foobar"
    assert d["foo"] == "foobar"

    assert compute_if_absent(d, "bar", lambda _: "backup-bar") == "real-bar"
    assert d["bar"] == "real-bar"

    assert d == {
        "bar": "real-bar",
        "foo": "foobar",
    }


def test_reverse_dict():
    d = {"A": "a", "B": "b"}

    d_id = id(d)
    reversed_d = reverse_dict(d)
    assert reversed_d == {"a": "A", "b": "B"}
    assert id(reversed_d) != d_id

    with pytest.raises(ValueError):
        reverse_dict({0: 0, 1: 0})


def test_flatten_dict(nested_dict, flattened_dict):
    actual = flatten_dict(nested_dict, string_fn="builtins.str")
    assert actual == flattened_dict


def test_flatten_dict_nonstandard_args():
    from datetime import date

    def filter_fn(key, value):
        if isinstance(key, date):
            return key.day % 2 == 0
        if isinstance(value, date):
            return value.day % 2 == 0
        return True

    d = {
        date(1999, 4, 30): {"morris": "tarzan", "another_odd_date": date(2019, 5, 11)},
        date(1991, 6, 5): "should-be-removed",
        "keep me": {"please": "thank you"},
    }
    actual = flatten_dict(d, filter_predicate=filter_fn)
    assert actual == {"1999-04-30.morris": "tarzan", "keep me.please": "thank you"}

    with pytest.raises(TypeError, match="string_fn=None"):
        flatten_dict(d, filter_predicate=filter_fn, string_fn=None)


def test_unflatten_dict(nested_dict, flattened_dict):
    actual = unflatten_dict(flattened_dict)
    assert actual == nested_dict


def test_unflatten_dict_tuples(nested_dict, flattened_dict):
    flattened_dict = {tuple(k.split(".")): v for k, v in flattened_dict.items()}
    actual = unflatten_dict(flattened_dict)
    assert actual == nested_dict


def test_flatten_dict_false_values_only(nested_dict):
    actual = flatten_dict(
        nested_dict,
        filter_predicate=lambda _, value: isinstance(value, dict) or not value,
    )

    expected = {
        "top-key0.mid-key1.bot-key1": False,
        "top-key2": False,
        "top-key3.mid-key1.bot-key1.extra-bot-key1.extra-extra-bot-key1": False,
    }
    assert actual == expected


@pytest.fixture
def nested_dict():
    return {
        "top-key0": {
            "mid-key0": True,
            "mid-key1": {"bot-key0": True, "bot-key1": False},
        },
        "top-key1": {"mid-key0": True, "mid-key1": True},
        "top-key2": False,
        "top-key3": {
            "mid-key0": True,
            "mid-key1": {
                "bot-key0": True,
                "bot-key1": {
                    "extra-bot-key0": True,
                    "extra-bot-key1": {
                        "extra-extra-bot-key0": True,
                        "extra-extra-bot-key1": False,
                    },
                },
            },
        },
        "top-key4": True,
    }


@pytest.fixture
def flattened_dict():
    return {
        "top-key0.mid-key0": True,
        "top-key0.mid-key1.bot-key0": True,
        "top-key0.mid-key1.bot-key1": False,
        "top-key1.mid-key0": True,
        "top-key1.mid-key1": True,
        "top-key2": False,
        "top-key3.mid-key0": True,
        "top-key3.mid-key1.bot-key0": True,
        "top-key3.mid-key1.bot-key1.extra-bot-key0": True,
        "top-key3.mid-key1.bot-key1.extra-bot-key1.extra-extra-bot-key0": True,
        "top-key3.mid-key1.bot-key1.extra-bot-key1.extra-extra-bot-key1": False,
        "top-key4": True,
    }


@pytest.fixture
def ikd():
    return InheritedKeysDict.make(
        dict(
            default={0: "shared0", 1: "shared1"},
            specific={
                "ctx0": {0: "c0-v0"},
                "ctx1": {0: "c1-v0", 1: "c1-v1"},
            },
        )
    )


def test_inherited_keys_dict(ikd):
    assert ikd["ctx0"] == {0: "c0-v0", 1: "shared1"}
    assert ikd["ctx1"] == {0: "c1-v0", 1: "c1-v1"}
    assert ikd["not-in-d"] == {0: "shared0", 1: "shared1"}
    assert len(ikd) == 2
    assert list(ikd) == ["ctx0", "ctx1"]

    with pytest.raises(KeyError):
        empty: InheritedKeysDict[str, str, str] = InheritedKeysDict()
        _ = empty["any-key-will-do"]


def test_copy_inherited_keys_dict(ikd):
    assert ikd == ikd.copy()


class TestDictComparer:
    def test_added_only(self):
        dc = DictComparer({-1: None, 1: 1}, baseline={i: i for i in range(3)})
        assert dc.total == 3
        assert dc.changed == {-1: None, 0: 0, 2: 2}
        assert dc.added == {-1: None}

    @pytest.mark.parametrize("preference", ["old", "new"])
    def test_updated_only(self, preference):
        if preference == "new":
            expected_zero_value = None
        else:
            expected_zero_value = 0
        expected_str = f"updated(1): {{0: {expected_zero_value}}}, removed(1): {{2}}"

        dc = DictComparer({0: None, 1: 1}, baseline={i: i for i in range(3)}, preference=preference)
        assert dc.preference == preference
        assert dc.total == 2
        assert dc.changed == {0: expected_zero_value, 2: 2}
        assert dc.updated == {0: expected_zero_value}
        assert dc.to_string() == expected_str

    def test_removed_only(self):
        dc = DictComparer({0: None, 1: 1}, baseline={i: i for i in range(3)})
        assert dc.total == 2
        assert dc.changed == {0: None, 2: 2}
        assert dc.removed == {2: 2}
        assert dc.to_string() == "updated(1): {0: None}, removed(1): {2}"

    def test_all(self):
        dc = DictComparer({0: None, 1: 1, -1: None}, baseline={i: i for i in range(3)})
        assert dc.preference == "new"

        assert dc.total == 3
        assert len(dc.changed) == dc.total
        assert len(dc.changed) == len(dc.added) + len(dc.updated) + len(dc.removed)

        assert dc.added == {-1: None}, dc.added
        assert dc.updated == {0: None}, dc.updated
        assert dc.removed == {2: 2}, dc.removed
        assert dc.changed == {-1: None, 0: None, 2: 2}
        assert dc.to_string() == "added(1): {-1: None}, updated(1): {0: None}, removed(1): {2}"

    def test_wrapper(self):
        actual = DictComparer({"foo": {"bar": 1}, "baz": 0}, baseline={"foo": 1, "bar": None}).to_string(flatten=True)
        assert actual == "added(1): {'baz': 0}, updated(1): {'foo.bar': 1}, removed(1): {'bar'}"
