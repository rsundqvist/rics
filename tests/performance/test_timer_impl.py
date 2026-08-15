"""Tests for the timing loop and the memory guarantee it has to uphold; see ``rics.performance._timer``."""

import gc
from typing import Any

import pytest

from rics.performance import MultiCaseTimer, _timer

# These tests calibrate with tiny budgets, which can emit a benign "Results may be unreliable" warning.
pytestmark = pytest.mark.filterwarnings("ignore:Results may be unreliable:UserWarning")


@pytest.fixture(params=[False, True], ids=["stdlib", "experimental"])
def experimental(request, monkeypatch):
    """Run the test against both timer implementations; see RICS_PERF_EXPERIMENTAL_TIMER."""
    monkeypatch.setattr(_timer, "USE_EXPERIMENTAL_TIMER", request.param)
    return request.param


class Tracked:
    """Counts how many instances are alive at once."""

    live = 0
    peak = 0

    def __init__(self) -> None:
        Tracked.live += 1
        Tracked.peak = max(Tracked.peak, Tracked.live)

    def __del__(self) -> None:
        Tracked.live -= 1

    @classmethod
    def reset(cls) -> None:
        gc.collect()
        cls.live = cls.peak = 0


def count_collections(timer: "MultiCaseTimer[Any, *tuple[Any, ...]]") -> int:
    """Run `timer`, returning the number of collections it triggered."""
    collections = {"n": 0}

    def callback(phase, _info):
        if phase == "start":
            collections["n"] += 1

    gc.callbacks.append(callback)
    gc.disable()  # Only *explicit* collections can fire the callback now.
    try:
        timer.run(time_per_candidate=0.01, repeat=1)
    finally:
        gc.enable()
        gc.callbacks.remove(callback)

    return collections["n"]


def test_timer_semantics(experimental):  # noqa: ARG001
    counts = {"calls": 0, "setups": 0}

    def candidate(_data):
        counts["calls"] += 1

    def setup(data):
        counts["setups"] += 1
        return data

    timings = _timer.make_timer(candidate, [1, 2], setup).repeat(3, 100)

    assert len(timings) == 3
    assert counts["calls"] == 3 * 100
    assert counts["setups"] == 3  # Untimed, once per repetition -- as in timeit.Timer.
    assert gc.isenabled()  # Restored after timing.


@pytest.mark.parametrize(
    "skip_if",
    [
        None,
        lambda params: False,  # noqa: ARG005
        lambda params: params.data_label[0] % 2 == 0,  # Also covers the skipped-combination path.
    ],
    ids=["no-skip_if", "skip-none", "skip-every-other"],
)
def test_at_most_one_variant_alive(experimental, skip_if):  # noqa: ARG001
    # Automatic collection is disabled to make the assertion deterministic: retention then shows up as a peak > 1
    # instead of being cleaned up by chance.
    Tracked.reset()
    timer = MultiCaseTimer(lambda _d: None, lambda _i: Tracked(), case_args=[(i,) for i in range(4)])

    gc.disable()
    try:
        # No explicit number, so calibration runs several rounds.
        timer.run(time_per_candidate=0.01, repeat=1, skip_if=skip_if)
    finally:
        gc.enable()

    assert Tracked.peak == 1
    Tracked.reset()


def test_collections_are_only_needed_for_the_stdlib_timer(experimental):
    timer = MultiCaseTimer(lambda _d: None, lambda i: [i], case_args=[(i,) for i in range(4)])

    if experimental:
        assert count_collections(timer) == 0  # No cycles to break.
    else:
        assert count_collections(timer) > 0  # Explicit collections are what uphold the guarantee.


def test_dict_test_data_never_collects(experimental):  # noqa: ARG001
    # Every variant is alive by construction, so there is nothing to reclaim and nothing to pay for.
    timer: MultiCaseTimer[list[int]] = MultiCaseTimer(lambda _d: None, test_data={i: [i] for i in range(4)})

    assert count_collections(timer) == 0
