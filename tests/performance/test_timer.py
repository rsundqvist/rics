from collections import defaultdict

import pytest

from rics.performance import MultiCaseTimer, SkipIfParams

# These tests calibrate with tiny budgets, which can emit a benign "Results may be unreliable" warning.
pytestmark = pytest.mark.filterwarnings("ignore:Results may be unreliable:UserWarning")


def test_skip():
    calls: dict[int, int] = defaultdict(int)

    def func(data):
        calls[data] += 1

    def skip_if(params: SkipIfParams[int]) -> bool:
        return params.data == 2

    run_results = MultiCaseTimer[int](func, test_data=[1, 2, 3]).run(number=2, skip_if=skip_if)

    label = "test_skip.<locals>.func"
    assert [*run_results] == [label]
    assert [*run_results[label]] == ["1", "3"]
    assert calls == {1: 10, 3: 10}


def test_skip_during_autonumber():
    def func(data):
        if data == "bad":
            raise RuntimeError("must never be called for 'bad'")
        return sum(range(50))

    def skip_if(params: SkipIfParams[str]) -> bool:
        return params.data == "bad"

    run_results = MultiCaseTimer[str](func, test_data=["ok", "bad"]).run(time_per_candidate=0.01, skip_if=skip_if)

    label = "test_skip_during_autonumber.<locals>.func"
    assert [*run_results[label]] == ["ok"]


def test_skip_all_variants_for_candidate(caplog):
    # Every variant skipped -> no timing, no infinite loop in autonumber.
    run_results = MultiCaseTimer[int](lambda data: data, test_data=[1, 2]).run(
        time_per_candidate=0.01,
        skip_if=lambda _: True,
    )
    assert not run_results
    assert "Discarding candidate" in caplog.text
