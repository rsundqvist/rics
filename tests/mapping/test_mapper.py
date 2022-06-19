import pytest

from rics.cardinality import Cardinality
from rics.mapping import Mapper
from rics.mapping.exceptions import MappingError


def _substring_score(k, c):
    for ci in c:
        yield float(k in ci) / len(ci)


def test_default():
    mapper = Mapper(("a", "ab", "b"))
    assert mapper.apply(["a"]).left_to_right == {"a": ("a",)}
    assert mapper.apply(["b"]).left_to_right == {"b": ("b",)}
    assert mapper.apply(["a", "b"]).left_to_right == {"a": ("a",), "b": ("b",)}


def test_with_overrides():
    mapper = Mapper(("a", "ab", "b"), overrides={"a": "fixed"})
    assert mapper.apply(["a"]).left_to_right == {"a": ("fixed",)}
    assert mapper.apply(["b"]).left_to_right == {"b": ("b",)}
    assert mapper.apply(["a", "b"]).left_to_right == {"a": ("fixed",), "b": ("b",)}


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
def test_multiple_matches(values, expected, allow_multiple):
    mapper = Mapper(
        ("a", "ab", "b"),
        min_score=0.1,
        score_function=_substring_score,
        cardinality=None if allow_multiple else Cardinality.OneToOne,
    )
    assert mapper.apply(values).left_to_right == expected


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
def test_multiple_matches_with_overrides(values, expected, allow_multiple):
    mapper = Mapper(
        candidates=("a", "ab", "b"),
        overrides={"a": "fixed"},
        min_score=0.1,
        score_function=_substring_score,
        cardinality=None if allow_multiple else Cardinality.OneToOne,
    )
    assert mapper.apply(values).left_to_right == expected


def test_failure():
    with pytest.raises(MappingError):
        Mapper(candidates=(1, 2), unmapped_values_action="raise").apply((3, 4))


@pytest.mark.parametrize(
    "filters, expected",
    [
        (
            [
                # Removes "b" as a candidate
                ("shortlisted_substring_in_candidate", dict(substrings=["a"]))
            ],
            {"a": ("a", "ab"), "b": ("b", "ab")},
        ),
        (
            [
                # Removes "b" and "ab" as a candidate
                ("shortlisted_substring_in_candidate", dict(substrings=["a"])),
                ("banned_substring_in_name", dict(substrings=["b"])),
            ],
            {"a": ("a", "ab")},
        ),
        (
            [
                # Removes all candidates
                ("banned_substring_in_name", dict(substrings=list("abc"))),
            ],
            {},
        ),
    ],
)
def test_filter(filters, expected):
    mapper = Mapper(
        candidates=("a", "ab", "b"),
        min_score=0.1,
        score_function=_substring_score,
        filter_functions=filters,
        cardinality=Cardinality.ManyToMany,  # Anything goes
    )

    actual = mapper.apply("abc").left_to_right
    assert actual == expected
