import pytest

from rics.mapping import filter_functions as mf

KEYWORDS = ("or", "ee")


def test__parse_where_arg():
    with pytest.raises(ValueError):
        mf._parse_where_arg("bad-arg")

    assert mf._parse_where_arg("name")
    assert not mf._parse_where_arg("candidate")
    assert mf._parse_where_arg("both")


@pytest.mark.parametrize(
    "name, candidates, where, expected",
    [
        # where: name
        ("pre-name", {"cand0", "cand1"}, "name", {"cand0", "cand1"}),
        ("name", {"pre-cand0", "pre-cand1"}, "name", set()),
        # where: candidate
        ("pre-name", {"pre-cand0", "pre-cand1"}, "candidate", {"pre-cand0", "pre-cand1"}),
        ("pre-name", {"pre-cand0", "cand1"}, "candidate", {"pre-cand0"}),
        ("pre-name", {"cand0", "cand1"}, "candidate", set()),
        # where: both
        ("pre-name", {"pre-cand0", "pre-cand1"}, "both", {"pre-cand0", "pre-cand1"}),
        ("pre-name", {"pre-cand0", "cand1"}, "both", {"pre-cand0"}),
        ("name", {"pre-cand0", "pre-cand1"}, "both", set()),
        ("pre-name", {"cand0", "cand1"}, "both", set()),
    ],
    ids=[
        "where-name-hit",
        "where-name-miss",
        "where-cand-2-hit",
        "where-cand-1-hit",
        "where-cand-miss",
        "where-both-2-hit",
        "where-both-1-hit",
        "where-both-name-miss",
        "where-both-cand-miss",
    ],
)
def test_require_prefix(name, candidates, where, expected):
    actual = mf.require_prefix(name, candidates, prefix="pre", where=where)
    assert actual == expected


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
        # where: both
        ("name-suf", {"cand0-suf", "cand1-suf"}, "both", {"cand0-suf", "cand1-suf"}),
        ("name-suf", {"cand0-suf", "cand1"}, "both", {"cand0-suf"}),
        ("name", {"cand0-suf", "cand1-suf"}, "both", set()),
        ("name-suf", {"cand0", "cand1"}, "both", set()),
    ],
    ids=[
        "where-name-hit",
        "where-name-miss",
        "where-cand-2-hit",
        "where-cand-1-hit",
        "where-cand-miss",
        "where-both-2-hit",
        "where-both-1-hit",
        "where-both-name-miss",
        "where-both-cand-miss",
    ],
)
def test_require_suffix(name, candidates, where, expected):
    actual = mf.require_suffix(name, candidates, suffix="suf", where=where)
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
        # where: both
        ("torque", "both", ["more", "torque", "a"], set()),
        ("abc", "both", ["more", "torque", "a"], {"a"}),
    ],
)
def test_banned_substring(name, where, candidates, expected):
    actual = mf.banned_substring(name, candidates=candidates, substrings=KEYWORDS, where=where)
    assert actual == expected


@pytest.mark.parametrize(
    "name, candidates, expected",
    [
        ("torque", set("abc"), set("abc")),
        ("abc", ["more", "torque"], {"more", "torque"}),
        ("unforeseeable", ["a", "more", "whee"], {"more", "whee"}),
        ("store", ["a", "more", "whee"], {"more"}),
        ("store", ["a", "more", "before"], {"more", "before"}),
    ],
    ids=["not-in-candidates", "not-in-name", "both-in-name", "one-in-name", "one-in-two-candidates"],
)
def test_shortlisted_substring_in_candidate(name, candidates, expected):
    actual = mf.shortlisted_substring_in_candidate(name, candidates, substrings=KEYWORDS)
    assert actual == expected
