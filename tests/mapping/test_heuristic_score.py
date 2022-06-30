import pytest

from rics.mapping import HeuristicScore

inf = float("inf")


@pytest.fixture(scope="module")
def heuristic_score():
    heuristics = [
        ("short_circuit_to_value", dict(regex=".*MATCH$", target="TARGET_VALUE")),
        ("force_lower_case", {}),
    ]
    ans = HeuristicScore("equality", heuristics)
    ans.add_heuristic("value_fstring_alias", dict(fstring="prefixed_{value}"))  # Add coverage
    return ans


@pytest.mark.parametrize(
    "value, candidates, expected",
    [
        ("TARGET_VALUE", ["cand0", "cand1"], [0, 0]),
        ("CAND0", ["cand0", "cand1"], [1, 0]),
        ("TARGET_VALUE", ["cand0", "correct_MATCH"], [-inf, inf]),
        ("TARGET_VALUE", ["cand0", "correct_match", "MATCH_but_not_quite_right"], [-inf, inf, -inf]),
        ("VALUE", ["cand0", "prefixed_value", "prefixed", "prefixed_VALUE"], [0, 0, 0, 1]),
    ],
)
def test_heuristic_score(value, candidates, expected, heuristic_score):
    actual = list(heuristic_score(value, candidates, None))
    assert actual == expected
