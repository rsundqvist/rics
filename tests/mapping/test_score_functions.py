import pandas as pd
import pytest
from numpy.random import choice, randint

from rics.mapping import score_functions


@pytest.mark.parametrize(
    "value, expected_max_table",
    [
        ("human_id", "humans"),
        ("human", "humans"),
        ("animal", "animals"),
        ("animals_id", "animals"),
    ],
)
def test_like_database_table(value, expected_max_table):
    candidate_tables = ["humans", "animals"]
    score = score_functions.get("like_database_table")

    s = pd.Series(score(value, candidate_tables, True), index=candidate_tables)
    assert s.idxmax() == expected_max_table, s.values


@pytest.mark.parametrize(
    "func, dtype",
    [
        ("like_database_table", str),
        ("modified_hamming", str),
        ("equality", str),
        ("equality", int),
    ],
)
def test_stable(func, dtype):
    """Score function should respect input order."""
    if func == "like_database_table" and dtype != str:
        return

    score = score_functions.get(func)

    candidates = make(12, dtype)
    values = make(6, dtype)

    for v in values:
        actual_scores = list(score(v, candidates.copy()))

        assert all([isinstance(s, float) for s in actual_scores]), "Bad return type"

        expected_scores = [next(score(v, [candidates[i]])) for i in range(len(candidates))]

        assert actual_scores == expected_scores


def make(count, dtype):
    if dtype == int:
        return make_int(count)
    if dtype == str:
        return make_str(count)
    raise AssertionError


def make_str(count):
    ans = []

    for i in range(count):
        joiner = ["-", "_"][i % 2]
        ans.append(joiner.join(choice(WORDS, randint(1, 4))))

    return ans


def make_int(count):
    return list(randint(-10, 10, count))


WORDS = [
    "party",
    "favor",
    "blue",
    "snap",
    "doubt",
    "major",
    "exploration",
    "brush",
    "self",
    "collection",
    "casualty",
    "east",
    "comment",
    "index",
    "throw",
    "referral",
    "disorder",
    "sermon",
    "sleeve",
    "institution",
    "house",
    "cassette",
    "tree",
    "prayer",
    "damn",
    "heir",
    "redeem",
    "complication",
    "squeeze",
    "contact",
]
