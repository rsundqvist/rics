import pytest

from rics.mapping import heuristic_functions as hf


@pytest.mark.parametrize(
    "value, candidates, expected",
    [
        ("target-miss", ["MATCH0", "MATCH1"], []),
        ("TARGET", ["wrong0", "wrong1"], []),
        ("TARGET", ["MATCH0", "wrong1"], ["MATCH0"]),
        ("TARGET", ["MATCH0", "wrong1", "MATCH1"], ["MATCH0", "MATCH1"]),
    ],
)
def test_short_circuit_to_value(value, candidates, expected):
    actual = sorted(list(hf.short_circuit_to_value(value, candidates, None, ".*MATCH.*", target="TARGET")))
    assert actual == expected


@pytest.mark.parametrize(
    "value, add_target, expected",
    [
        ("match", False, []),
        ("miss", True, []),
        ("match", True, ["TARGET"]),
    ],
)
def test_short_circuit_to_candidate(value, add_target, expected):
    candidates = ["cand"]
    if add_target:
        candidates.append("TARGET")
    actual = list(hf.short_circuit_to_candidate(value, candidates, None, ".*MATCH.*", target="TARGET"))
    assert actual == expected


@pytest.mark.parametrize(
    "fstring, expected_value",
    [
        ("no-kwarg", "no-kwarg"),
        ("{value}", "VALUE"),
        ("{value}_{kwarg}", "VALUE_KWARG"),
        ("only {kwarg}", "only KWARG"),
    ],
)
def test_value_fstring_alias(fstring, expected_value):
    candidates = list("abc")
    actual_value, actual_candidates = hf.value_fstring_alias("VALUE", candidates.copy(), None, fstring, kwarg="KWARG")

    assert actual_value == expected_value
    assert actual_candidates == candidates


@pytest.mark.parametrize(
    "fstring, expected_candidates",
    [
        ("no-kwarg", ["no-kwarg"] * 2),
        ("{candidate}", ["CAND0", "CAND1"]),
        ("{candidate}_{kwarg}", ["CAND0_KWARG", "CAND1_KWARG"]),
        ("only {kwarg}", ["only KWARG"] * 2),
    ],
)
def test_candidate_fstring_alias(fstring, expected_candidates):
    candidates = ["CAND0", "CAND1"]
    actual_value, actual_candidates = hf.candidate_fstring_alias("VALUE", candidates, None, fstring, kwarg="KWARG")

    assert candidates == ["CAND0", "CAND1"]
    assert actual_value == "VALUE"
    assert list(actual_candidates) == expected_candidates
