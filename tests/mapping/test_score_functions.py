import pandas as pd
import pytest
from numpy import inf
from numpy.random import choice, randint

from rics.mapping import score_functions as sf

with open("tests/mapping/words.txt") as f:
    WORDS = f.read().splitlines()


def test_from_bad_name():
    with pytest.raises(ValueError):
        sf.from_name("does-not-exist")


@pytest.mark.parametrize(
    "value, add_source, expected",
    [
        ("id", False, [False, False, False, False, False]),
        ("id", True, [True, False, False, False, False]),
        ("name", False, [False, False, False, True, True]),
        ("exact", True, [False, True, False, False, False]),
    ],
)
def test_score_with_heuristics(value, add_source, expected):
    columns = ["animal_id", "exact", "exact_animal", "cute_name", "name_real"]

    fstrings = ["{value}_real", "cute_{value}"]
    if add_source:
        fstrings.append("{source}_{value}")

    actual = list(
        sf.score_with_heuristics(
            value,
            columns,
            source="animal",  # Given by mapper
            # Configured
            fstrings=fstrings,
        )
    )
    actual_above_05 = [v > 0.5 for v in actual]
    assert actual_above_05 == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        ("cand", [1.0, 0.0, 0.0, 0.0]),
        ("cand0", [-inf, inf, -inf, inf]),
        ("cand2", [-inf, inf, inf, inf]),
    ],
    # ids=["no-cs-1", "no-cs-2", "kw1-cs", "kw2-cs", "kw1/kw2-cs"],
)
def test_score_with_heuristics_short_circuiting(value, expected):
    kwargs = {
        "cand0": [".*kw1.*"],
        "cand2": [".*kw1.*", ".*kw2.*"],
    }
    candidates = ["cand", "cand-kW1", "cand-KW2", "cand-kW1-kw2"]

    actual = list(sf.score_with_heuristics(value, candidates, **kwargs))
    assert actual == expected


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

    s = pd.Series(score(value, candidate_tables), index=candidate_tables)
    assert s.idxmax() == expected_max_table, s


@pytest.mark.parametrize(
    "func, dtype", [(func, str) for func in sf._all_functions] + [(sf.equality, int)]  # type: ignore
)
def test_stable(func, dtype):
    """Score function should respect input order."""
    candidates = make(12, dtype)
    values = make(6, dtype)

    kwargs = {"fstrings": ["un_{value}"]} if func == sf.score_with_heuristics else {}

    for v in values:
        actual_scores = list(func(v, candidates.copy(), **kwargs))
        assert all([isinstance(s, float) for s in actual_scores]), "Bad return type"

        expected_scores = [next(iter(func(v, [candidates[i]], **kwargs))) for i in range(len(candidates))]
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
