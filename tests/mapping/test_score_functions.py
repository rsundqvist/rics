import pytest
from numpy.random import choice, randint

from rics.mapping import score_functions as sf

with open("tests/mapping/words.txt") as f:
    WORDS = f.read().splitlines()

SCORE_FUNCTIONS = [sf.equality, sf.modified_hamming]


@pytest.mark.parametrize("func, dtype", [(func, str) for func in SCORE_FUNCTIONS] + [(sf.equality, int)])
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
