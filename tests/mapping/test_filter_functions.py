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
    "name, source, candidates, where, expected",
    [
        # where: name
        ("name-suf", "", {"cand0", "cand1"}, "name", {"cand0", "cand1"}),
        ("name", "", {"cand0-suf", "cand1-suf"}, "name", set()),
        # where: candidate
        ("name-suf", "", {"cand0-suf", "cand1-suf"}, "candidate", {"cand0-suf", "cand1-suf"}),
        ("name-suf", "", {"cand0-suf", "cand1"}, "candidate", {"cand0-suf"}),
        ("name-suf", "", {"cand0", "cand1"}, "candidate", set()),
        # where: name + candidate
        ("name-suf", "", {"cand0-suf", "cand1-suf"}, ("name", "candidate"), {"cand0-suf", "cand1-suf"}),
        ("name-suf", "", {"cand0-suf", "cand1"}, ("name", "candidate"), {"cand0-suf"}),
        ("name", "", {"cand0-suf", "cand1-suf"}, ("name", "candidate"), set()),
        ("name-suf", "", {"cand0", "cand1"}, ("name", "candidate"), set()),
        # where: source
        ("whatever", "source-suf", {"cand0", "cand1"}, "source", {"cand0", "cand1"}),
        ("whatever", "source", {"cand0-suf", "cand1-suf"}, "source", set()),
        # where: name + source
        ("name", "source-suf", {"cand0-suf", "cand1-suf"}, ("name", "source"), set()),
        ("name-suf", "source", {"cand0-suf", "cand1-suf"}, ("name", "source"), set()),
        ("name-suf", "source-suf", {"cand0-suf", "cand1-suf"}, ("name", "source"), {"cand0-suf", "cand1-suf"}),
        ("name-suf", "source-suf", {"cand0-suf", "cand1"}, ("name", "source", "candidate"), {"cand0-suf"}),
    ],
    ids=[
        "where-name-hit",
        "where-name-miss",
        "where-cand-2-hit",
        "where-cand-1-hit",
        "where-cand-miss",
        "where-name/cand-2-hit",
        "where-name/cand-1-hit",
        "where-name/cand-name-miss",
        "where-name/cand-cand-miss",
        "where-source-hit",
        "where-source-miss",
        "where-name/source-miss1",
        "where-name/source-miss2",
        "where-name/source-hit",
        "where-name/source/cand-hit",
    ],
)
def test_require_regex_match(name, source, candidates, where, expected):
    actual = mf.require_regex_match(name, candidates, regex=".*suf$", where=where, source=source)
    assert actual == expected


@pytest.mark.parametrize(
    "name, source, where, candidates, expected",
    [
        # where: name
        ("torque", "", "name", set("abc"), set()),
        ("abc", "", "name", ["more", "torque"], {"more", "torque"}),
        # where: candidate
        ("torque", "", "candidate", set("abc"), set("abc")),
        ("abc", "", "candidate", ["more", "torque"], set()),
        # where: name + candidate
        ("torque", "", ("name", "candidate"), ["more", "torque", "a"], set()),
        ("abc", "", ("name", "candidate"), ["more", "torque", "a"], {"a"}),
        # where: source
        ("", "torque", "source", set("abc"), set()),
        ("", "abc", "source", ["more", "torque"], {"more", "torque"}),
    ],
)
def test_banned_substring(name, source, where, candidates, expected):
    actual = mf.banned_substring(name, candidates=candidates, substrings=KEYWORDS, where=where, source=source)
    assert actual == expected
