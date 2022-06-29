import pandas as pd
import pytest
from numpy.random import choice, randint

from rics.mapping import score_functions as sf

with open("tests/mapping/words.txt") as f:
    WORDS = f.read().splitlines()


def test_from_bad_name():
    with pytest.raises(ValueError):
        sf.from_name("does-not-exist")


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
    score = sf.from_name("like_database_table")

    s = pd.Series(score(value, candidate_tables, None), index=candidate_tables)
    assert s.idxmax() == expected_max_table, s


@pytest.mark.parametrize(
    "func, dtype", [(func, str) for func in sf._all_functions] + [(sf.equality, int)]  # type: ignore
)
def test_stable(func, dtype):
    """Score function should respect input order."""
    candidates = make(12, dtype)
    values = make(6, dtype)

    for v in values:
        actual_scores = list(func(v, candidates.copy(), None))
        assert all([isinstance(s, float) for s in actual_scores]), "Bad return type"

        expected_scores = [next(iter(func(v, [candidates[i]], None))) for i in range(len(candidates))]
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
