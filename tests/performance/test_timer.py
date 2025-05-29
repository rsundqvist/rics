from collections import defaultdict

import pytest

from rics.performance import MultiCaseTimer, SkipIfParams


@pytest.mark.filterwarnings("ignore:Results may be unreliable:UserWarning")
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
