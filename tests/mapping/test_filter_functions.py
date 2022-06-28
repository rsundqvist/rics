import pytest

from rics.mapping import filter_functions as mf

KEYWORDS = ("or", "ee")


def test__parse_where_arg():
    with pytest.raises(ValueError):
        mf._parse_where_args("bad-arg")
    with pytest.raises(ValueError):
        mf._parse_where_args(())

    assert mf._parse_where_args(("name", "candidate", "source")) == ("name", "candidate", "source")
    assert mf._parse_where_args(("name", "source")) == ("name", "source")
    assert mf._parse_where_args("name") == ("name",)


@pytest.mark.parametrize(
    "name, candidates, where, expected",
    [
        # where: name
        ("name-suf", {"cand0", "cand1"}, "name", {"cand0", "cand1"}),
        ("name", {"cand0-suf", "cand1-suf"}, "name", set()),
        # where: candidate
        ("name-suf", {"cand0-suf", "cand1-suf"}, "candidate", {"cand0-suf", "cand1-suf"}),
        ("name-suf", {"cand0-suf", "cand1"}, "candidate", {"cand0-suf"}),
        ("name-suf", {"cand0", "cand1"}, "candidate", set()),
        # where: name + candidate
        ("name-suf", {"cand0-suf", "cand1-suf"}, ("name", "candidate"), {"cand0-suf", "cand1-suf"}),
        ("name-suf", {"cand0-suf", "cand1"}, ("name", "candidate"), {"cand0-suf"}),
        ("name", {"cand0-suf", "cand1-suf"}, ("name", "candidate"), set()),
        ("name-suf", {"cand0", "cand1"}, ("name", "candidate"), set()),
    ],
    ids=[
        "where-name-hit",
        "where-name-miss",
        "where-cand-2-hit",
        "where-cand-1-hit",
        "where-cand-miss",
        "where-name-and-cand-2-hit",
        "where-name-and-cand-1-hit",
        "where-name-and-cand-name-miss",
        "where-name-and-cand-cand-miss",
    ],
)
def test_require_regex_match(name, candidates, where, expected):
    actual = mf.require_regex_match(name, candidates, regex=".*suf$", where=where)
    assert actual == expected


@pytest.mark.parametrize(
    "name, where, candidates, expected",
    [
        # where: name
        ("torque", "name", set("abc"), set()),
        ("abc", "name", ["more", "torque"], {"more", "torque"}),
        # where: candidate
        ("torque", "candidate", set("abc"), set("abc")),
        ("abc", "candidate", ["more", "torque"], set()),
        # where: name + candidate
        ("torque", ("name", "candidate"), ["more", "torque", "a"], set()),
        ("abc", ("name", "candidate"), ["more", "torque", "a"], {"a"}),
    ],
)
def test_banned_substring(name, where, candidates, expected):
    actual = mf.banned_substring(name, candidates=candidates, substrings=KEYWORDS, where=where)
    assert actual == expected
