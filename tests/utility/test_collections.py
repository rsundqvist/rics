import pytest

from rics.utility.collections import compute_if_absent, flatten_dict, reverse_dict


def test_compute_if_absent():
    d = {"bar": "real-bar"}

    with pytest.raises(KeyError):
        compute_if_absent(d, "foo")
    assert "foo" not in d

    assert compute_if_absent(d, "foo", "{}bar".format) == "foobar"
    assert d["foo"] == "foobar"

    assert compute_if_absent(d, "bar", lambda s: "backup-bar") == "real-bar"
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

    ans = reverse_dict(d, inplace=True)
    assert ans is None
    assert reversed_d == {"a": "A", "b": "B"}


def test_flatten_dict(nested_dict):
    actual = flatten_dict(nested_dict)

    expected = {
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
    assert actual == expected


def test_flatten_dict_false_values_only(nested_dict):
    actual = flatten_dict(nested_dict, filter_predicate=lambda key, value: isinstance(value, dict) or not value)

    expected = {
        "top-key0.mid-key1.bot-key1": False,
        "top-key2": False,
        "top-key3.mid-key1.bot-key1.extra-bot-key1.extra-extra-bot-key1": False,
    }
    assert actual == expected


@pytest.fixture
def nested_dict():
    return {
        "top-key0": {"mid-key0": True, "mid-key1": {"bot-key0": True, "bot-key1": False}},
        "top-key1": {"mid-key0": True, "mid-key1": True},
        "top-key2": False,
        "top-key3": {
            "mid-key0": True,
            "mid-key1": {
                "bot-key0": True,
                "bot-key1": {
                    "extra-bot-key0": True,
                    "extra-bot-key1": {"extra-extra-bot-key0": True, "extra-extra-bot-key1": False},
                },
            },
        },
        "top-key4": True,
    }
