import pytest

from rics.cardinality import Cardinality
from rics.mapping import Mapper, exceptions


def _substring_score(k, c, _):
    for ci in c:
        yield float(k in ci) / len(ci)


@pytest.fixture(scope="module")
def candidates():
    return "a", "ab", "b"


def test_default(candidates):
    mapper = Mapper()
    assert mapper(candidates, ["a"]).left_to_right == {"a": ("a",)}
    assert mapper(candidates, ["b"]).left_to_right == {"b": ("b",)}
    assert mapper(candidates, ["a", "b"]).left_to_right == {"a": ("a",), "b": ("b",)}


def test_with_overrides(candidates):
    mapper = Mapper(overrides={"a": "fixed"})
    assert mapper(["a"], candidates).left_to_right == {"a": ("fixed",)}
    assert mapper(["b"], candidates).left_to_right == {"b": ("b",)}
    assert mapper(["a", "b"], candidates).left_to_right == {"a": ("fixed",), "b": ("b",)}


@pytest.mark.parametrize(
    "values, expected, allow_multiple",
    [
        ("a", {"a": ("a", "ab")}, True),
        ("b", {"b": ("b", "ab")}, True),
        ("ab", {"a": ("a", "ab"), "b": ("b", "ab")}, True),
        ("a", {"a": ("a",)}, False),
        ("b", {"b": ("b",)}, False),
        ("ab", {"a": ("a",), "b": ("b",)}, False),
    ],
)
def test_multiple_matches(values, expected, allow_multiple, candidates):
    mapper = Mapper(
        min_score=0.1,
        score_function=_substring_score,
        cardinality=None if allow_multiple else Cardinality.OneToOne,
    )
    assert mapper(values, candidates).left_to_right == expected


@pytest.mark.parametrize(
    "values, expected, allow_multiple",
    [
        ("a", {"a": ("fixed",)}, True),
        ("b", {"b": ("b", "ab")}, True),
        ("ab", {"a": ("fixed",), "b": ("b", "ab")}, True),
        ("a", {"a": ("fixed",)}, False),
        ("b", {"b": ("b",)}, False),
        ("ab", {"a": ("fixed",), "b": ("b",)}, False),
    ],
)
def test_multiple_matches_with_overrides(values, expected, allow_multiple, candidates):
    mapper = Mapper(
        overrides={"a": "fixed"},
        min_score=0.1,
        score_function=_substring_score,
        cardinality=None if allow_multiple else Cardinality.OneToOne,
    )
    assert mapper(values, candidates).left_to_right == expected


def test_mapping_failure(candidates):
    with pytest.raises(exceptions.MappingError):
        Mapper(unmapped_values_action="raise").apply((3, 4), candidates)


def test_bad_filter(candidates):
    with pytest.raises(exceptions.BadFilterError):
        Mapper(filter_functions=[(lambda *_: {3, 4}, {})]).apply((3, 4), candidates)


@pytest.mark.parametrize(
    "filters, expected",
    [
        (
            [
                # Removes "b" as a candidate
                ("require_regex_match", dict(regex="^a.*", where="candidate"))
            ],
            {"a": ("a", "ab"), "b": ("ab",)},
        ),
        (
            [
                # Removes "b" and "ab" as a candidate
                ("require_regex_match", dict(regex="^a.*", where="candidate")),
                ("banned_substring", dict(substrings="b", where="name")),
            ],
            {"a": ("a", "ab")},
        ),
        (
            [
                # Removes all candidates
                ("banned_substring", dict(substrings=list("abc"), where="name")),
            ],
            {},
        ),
    ],
)
def test_filter(filters, expected, candidates):
    mapper = Mapper(
        min_score=0.1,
        score_function=_substring_score,
        filter_functions=filters,
        cardinality=Cardinality.ManyToMany,  # Anything goes
    )

    actual = mapper("abc", candidates).left_to_right
    assert actual == expected
