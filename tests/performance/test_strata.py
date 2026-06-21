from collections import defaultdict
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Hashable

from rics.performance import MultiCaseTimer, Strata
from rics.performance._strata import build_strata, choose_auto_level, make_strata, resolve_stratify
from rics.performance.types import DataType

# These tests calibrate with tiny budgets, which can emit a benign "Results may be unreliable" warning.
pytestmark = pytest.mark.filterwarnings("ignore:Results may be unreliable:UserWarning")


def test_stratify_calibrates_number_per_stratum():
    # A cheap and an expensive variant. Without stratify they share one `number` (driven by the slow one), so both
    # get the same call count. With stratify, the fast variant earns a larger `number` -> strictly more calls.
    calls: dict[str, int] = defaultdict(int)

    def func(n):
        calls[f"n={n}"] += 1
        return sum(range(n))

    def run_and_count(**kwargs):
        calls.clear()
        MultiCaseTimer[int](func, test_data={"fast": 100, "slow": 100_000}).run(
            time_per_candidate=0.01, repeat=2, **kwargs
        )
        return dict(calls)

    shared = run_and_count()
    assert shared["n=100"] == shared["n=100000"]  # one shared number -> equal call counts

    stratified = run_and_count(stratify=lambda label: label)  # each variant is its own stratum
    assert stratified["n=100"] > stratified["n=100000"]  # fast variant is iterated more

    full = run_and_count(stratify="full")  # 'full' == one stratum per variant
    assert full["n=100"] > full["n=100000"]


def test_stratify_int_level_groups_by_case_args():
    # Tuple labels (size, kind); stratify by level 0 groups the two 'kind' variants of each size together.
    seen: dict[object, set[object]] = defaultdict(set)

    class RecordingTimer(MultiCaseTimer[DataType]):
        def _get_raw_timings(self, func, test_data, repeat, number, **kwargs):  # type: ignore[override]  # noqa: ARG002
            seen[test_data[0]].add(number)
            return [0.0] * repeat

    data = {(10, "a"): (10, "a"), (10, "b"): (10, "b"), (1000, "a"): (1000, "a")}
    RecordingTimer(lambda d: sum(range(d[0])), test_data=data).run(time_per_candidate=0.01, stratify=0)

    # Both size-10 variants share a calibrated number (one stratum); size-1000 is its own stratum.
    assert len(seen[10]) == 1


@pytest.mark.parametrize("bad", [True, "nope", 3.5])
def test_stratify_invalid(bad):
    with pytest.raises((TypeError, ValueError)):
        MultiCaseTimer[int](lambda d: d, test_data=[1, 2]).run(number=1, stratify=bad)


def test_stratify_auto_groups_by_cost_homogeneous_level():
    # (size, kind) labels: cost is driven by size, so grouping by level 0 keeps each stratum cost-homogeneous while
    # grouping by 'kind' would mix the cheap and expensive sizes. 'auto' must pick the size level.
    labels = [(100, "x"), (100, "y"), (1000, "x"), (1000, "y")]
    cost: dict[Hashable, float] = {(100, "x"): 1.0, (100, "y"): 1.2, (1000, "x"): 10.0, (1000, "y"): 12.0}
    strata = build_strata(labels, resolve_stratify("auto", labels, cost=cost))
    assert strata == {100: {(100, "x"), (100, "y")}, 1000: {(1000, "x"), (1000, "y")}}


def test_choose_auto_level_minimizes_worst_within_group_ratio():
    # Level 1 keeps the 10x size gap out of each group (ratio 1.2); level 0 would trap it (ratio 10).
    labels = [("a", 100), ("b", 100), ("a", 1000), ("b", 1000)]
    cost: dict[Hashable, float] = {("a", 100): 1.0, ("b", 100): 1.2, ("a", 1000): 10.0, ("b", 1000): 12.0}
    assert choose_auto_level(labels, range(2), cost) == 1


def test_choose_auto_level_breaks_ties_to_lowest_level():
    # Both levels separate the costs equally well -> the lowest level wins.
    labels = [(1, "a"), (2, "b")]
    cost: dict[Hashable, float] = {(1, "a"): 1.0, (2, "b"): 2.0}
    assert choose_auto_level(labels, range(2), cost) == 0


def test_choose_auto_level_ignores_uncosted_labels():
    # The size-1000 label has no cost (e.g. fully skipped) -> it does not influence the choice.
    labels = [(100, "x"), (100, "y"), (1000, "x")]
    cost: dict[Hashable, float] = {(100, "x"): 1.0, (100, "y"): 5.0}  # only level 1 separates these -> level 1
    assert choose_auto_level(labels, range(2), cost) == 1


def test_stratify_auto_without_cost_uses_first_level():
    # No cost measured (e.g. an explicit `number` makes grouping moot) -> fall back to the first viable level.
    labels = [(10, "a"), (10, "b"), (1000, "a")]
    strata = build_strata(labels, resolve_stratify("auto", labels, cost=None))
    assert strata == {10: {(10, "a"), (10, "b")}, 1000: {(1000, "a")}}


@pytest.mark.parametrize(
    "labels, match",
    [
        # Non-tuple labels can't be indexed by any level -> advise 'full' or a callable.
        pytest.param(["fast", "slow", "medium"], "not all data labels are tuples", id="non-tuple"),
        pytest.param([(10, "a"), "scalar", (20, "b")], "not all data labels are tuples", id="mixed"),
        # Single-level tuples have nothing for 'auto' to choose between -> advise the explicit first level.
        pytest.param([(10,), (1000,), (10,)], "stratify=0", id="single-level"),
    ],
)
def test_stratify_auto_raises_with_tailored_advice(labels, match):
    # 'auto' refuses unsuitable labels (rather than silently falling back) and points at the viable alternative.
    # Validation happens before any cost is consulted.
    with pytest.raises(ValueError, match=match):
        resolve_stratify("auto", labels)


def test_stratify_int_level_advises_full_or_callable_for_non_tuple():
    # An int level can only index tuples; a non-tuple label triggers advice toward 'full'/a callable.
    stratify = resolve_stratify(0, ["scalar"])
    assert stratify is not None
    with pytest.raises(TypeError, match="non-tuple labels"):
        stratify("scalar")


def test_stratify_int_level_advises_on_out_of_range_level():
    # A level beyond the tuple width reports the valid range instead of a bare IndexError.
    stratify = resolve_stratify(3, [(1, "a")])
    assert stratify is not None
    with pytest.raises(ValueError, match="only 2 level"):
        stratify((1, "a"))


def test_stratify_auto_calibrates_number_per_stratum():
    # End-to-end: 'auto' times each label, derives the size level from (size, kind) labels, and calibrates one
    # `number` per size. Sizes 10 and 100_000 differ in cost by orders of magnitude; the 'kind' does not.
    seen: dict[object, set[object]] = defaultdict(set)

    class RecordingTimer(MultiCaseTimer[DataType]):
        def _get_raw_timings(self, func, test_data, repeat, number, **kwargs):  # type: ignore[override]  # noqa: ARG002
            seen[test_data[0]].add(number)
            return [0.0] * repeat

    data = {(10, "a"): (10, "a"), (10, "b"): (10, "b"), (100_000, "a"): (100_000, "a")}
    RecordingTimer(lambda d: sum(range(d[0])), test_data=data).run(time_per_candidate=0.01, stratify="auto")

    # Both size-10 variants share a single calibrated number (one stratum); size-100_000 is its own stratum.
    assert len(seen[10]) == 1


def test_make_strata_records_how_it_was_fit():
    # make_strata returns a Strata that maps stratum_key -> labels, supports stratum_of, and records its source.
    labels = [(10, "a"), (10, "b"), (1000, "a")]
    strata = make_strata(labels, 0)
    assert isinstance(strata, Strata)
    assert dict(strata) == {10: frozenset({(10, "a"), (10, "b")}), 1000: frozenset({(1000, "a")})}
    assert strata.stratum_of((10, "b")) == 10
    assert strata.source == "level=0"
    assert strata.costs is None


def test_strata_records_auto_source_and_costs():
    labels = [(100, "x"), (100, "y"), (1000, "x"), (1000, "y")]
    cost: dict[Hashable, float] = {(100, "x"): 1.0, (100, "y"): 1.2, (1000, "x"): 10.0, (1000, "y"): 12.0}
    strata = make_strata(labels, "auto", cost=cost)
    assert strata.source == "auto(level=0)"  # size level chosen
    assert strata.costs == cost


def test_make_strata_accepts_a_plain_mapping():
    # Any mapping stratum_key -> labels is accepted, not just a Strata; it is wrapped and covers-checked.
    labels = [(10, "a"), (10, "b"), (1000, "a")]
    grouping = {"small": {(10, "a"), (10, "b")}, "big": [(1000, "a")]}
    strata = make_strata(labels, grouping)
    assert isinstance(strata, Strata)
    assert strata.source == "mapping"
    assert strata.stratum_of((10, "b")) == "small"
    assert strata.labels == frozenset(labels)


def test_make_strata_rejects_mapping_missing_labels():
    labels = [(10, "a"), (10, "b"), (1000, "a")]
    with pytest.raises(ValueError, match="does not cover every data label"):
        make_strata(labels, {"small": {(10, "a")}, "big": {(1000, "a")}})  # missing (10, "b")


def test_run_rejects_reused_strata_missing_labels():
    # A Strata reused on data it wasn't fit for must fail loudly (before timing), like the mapping path does.
    data = {(10, "a"): (10, "a"), (10, "b"): (10, "b"), (1000, "a"): (1000, "a")}
    timer: MultiCaseTimer[tuple[int, str]] = MultiCaseTimer(lambda d: sum(range(d[0])), test_data=data)
    strata = Strata({"small": {(10, "a"), (10, "b")}}, source="manual")  # missing (1000, "a")
    with pytest.raises(ValueError, match="does not cover every data label"):
        timer.run(time_per_candidate=0.01, stratify=strata)


def test_autonumber_probes_only_stratum_labels():
    # Calibration must materialize data only for the stratum being probed, not the whole dataset.
    import logging
    from functools import partial
    from timeit import Timer

    from rics.performance._autonumber import autonumber
    from rics.performance._generated_data import GeneratedData

    generated: list[int] = []

    def make(n: int) -> int:
        generated.append(n)
        return n

    data = GeneratedData(make, [(1,), (2,), (3,)], None, logging.getLogger("test"))

    autonumber(
        lambda d: d * d,
        "sq",
        data,
        {(2,)},  # only this stratum is probed
        time_allocation=0.0,  # return after the first measurement
        skip_if=None,
        make_timer=lambda f, d: Timer(partial(f, d)),
    )

    assert generated == [2]  # variants (1,) and (3,) were never generated


def test_run_accepts_a_plain_mapping_grouping():
    # A hand-built dict grouping drives calibration: both 'small' labels share one number.
    seen: dict[object, set[object]] = defaultdict(set)

    class StubTimer(MultiCaseTimer[DataType]):
        def _get_raw_timings(self, func, test_data, repeat, number, **kwargs):  # type: ignore[override]  # noqa: ARG002
            seen[test_data[0]].add(number)
            return [0.0] * repeat

    data = {(10, "a"): (10, "a"), (10, "b"): (10, "b"), (1000, "a"): (1000, "a")}
    grouping = {"small": {(10, "a"), (10, "b")}, "big": {(1000, "a")}}
    StubTimer(lambda d: sum(range(d[0])), test_data=data).run(time_per_candidate=0.01, stratify=grouping)

    assert len(seen[10]) == 1  # the two size-10 variants shared a single calibrated number


def test_compute_strata_is_reusable_without_reprobing():
    # compute_strata probes once; passing the result back to run() must not probe again.
    probes = {"n": 0}

    class CountingTimer(MultiCaseTimer[DataType]):
        def _new_timer(self, func, data):
            probes["n"] += 1
            return super()._new_timer(func, data)

        def _get_raw_timings(self, func, test_data, repeat, number, **kwargs):  # type: ignore[override]  # noqa: ARG002
            return [0.0] * repeat

    data = {(10, "a"): (10, "a"), (10, "b"): (10, "b"), (100_000, "a"): (100_000, "a")}
    timer = CountingTimer(lambda d: sum(range(d[0])), test_data=data)

    strata = timer.compute_strata("auto")
    assert strata.source == "auto(level=0)"
    after_fit = probes["n"]
    assert after_fit > 0  # the probe ran

    timer.run(number=1, stratify=strata)
    assert probes["n"] == after_fit  # reusing the grouping did not probe again


def test_fit_strata_caches_for_later_runs():
    # fit_strata populates the cache; a later run('auto') reuses that exact object (a re-probe would replace it).
    class StubTimer(MultiCaseTimer[DataType]):
        def _get_raw_timings(self, func, test_data, repeat, number, **kwargs):  # type: ignore[override]  # noqa: ARG002
            return [0.0] * repeat

    data = {(10, "a"): (10, "a"), (10, "b"): (10, "b"), (100_000, "a"): (100_000, "a")}
    timer = StubTimer(lambda d: sum(range(d[0])), test_data=data)

    timer.fit_strata("auto")
    strata = timer.strata
    assert timer._strata is strata  # cached on the instance

    timer.run(time_per_candidate=0.01, stratify="auto")
    assert timer._strata is strata  # reused, not re-fit


def test_compute_strata_does_not_cache():
    class StubTimer(MultiCaseTimer[DataType]):
        def _get_raw_timings(self, func, test_data, repeat, number, **kwargs):  # type: ignore[override]  # noqa: ARG002
            return [0.0] * repeat

    data = {(10, "a"): (10, "a"), (10, "b"): (10, "b"), (100_000, "a"): (100_000, "a")}
    timer = StubTimer(lambda d: sum(range(d[0])), test_data=data)

    timer.compute_strata("auto")  # pure: no side effects
    assert timer._strata is None


def test_run_auto_caches_strata_on_instance():
    # The first run('auto') fits and caches; a second run reuses the same Strata object.
    class StubTimer(MultiCaseTimer[DataType]):
        def _get_raw_timings(self, func, test_data, repeat, number, **kwargs):  # type: ignore[override]  # noqa: ARG002
            return [0.0] * repeat

    data = {(10, "a"): (10, "a"), (10, "b"): (10, "b"), (100_000, "a"): (100_000, "a")}
    timer = StubTimer(lambda d: sum(range(d[0])), test_data=data)

    timer.run(time_per_candidate=0.01, stratify="auto")
    cached = timer._strata
    assert cached is not None

    timer.run(time_per_candidate=0.01, stratify="auto")
    assert timer._strata is cached  # same object reused, not re-fit


def test_run_warns_when_reused_strata_skip_if_differs():
    strata = make_strata([(10, "a"), (1000, "a")], 0, skip_if=lambda params: False)  # noqa: ARG005

    class StubTimer(MultiCaseTimer[DataType]):
        def _get_raw_timings(self, func, test_data, repeat, number, **kwargs):  # type: ignore[override]  # noqa: ARG002
            return [0.0] * repeat

    data = {(10, "a"): (10, "a"), (1000, "a"): (1000, "a")}
    timer = StubTimer(lambda d: sum(range(d[0])), test_data=data)

    with pytest.warns(UserWarning, match="different skip_if|skip_if"):
        timer.run(number=1, stratify=strata)  # run's skip_if is None -> mismatch


def test_run_warns_when_reused_auto_strata_skip_if_differs():
    # A cached "auto" grouping reused under a different skip_if warns, just like an explicitly-passed Strata.
    class StubTimer(MultiCaseTimer[DataType]):
        def _get_raw_timings(self, func, test_data, repeat, number, **kwargs):  # type: ignore[override]  # noqa: ARG002
            return [0.0] * repeat

    data = {(10, "a"): (10, "a"), (1000, "a"): (1000, "a")}
    timer = StubTimer(lambda d: sum(range(d[0])), test_data=data)

    timer.fit_strata("auto", skip_if=lambda params: False)  # noqa: ARG005  # cache fit under one skip_if
    with pytest.warns(UserWarning, match="skip_if"):
        timer.run(time_per_candidate=0.01, stratify="auto", skip_if=None)  # reused under a different skip_if


def test_reused_strata_skip_if_warning_does_not_spam():
    # Fresh lambdas each fail the identity check, but the (informational) warning must fire at most once per instance.
    import warnings

    class StubTimer(MultiCaseTimer[DataType]):
        def _get_raw_timings(self, func, test_data, repeat, number, **kwargs):  # type: ignore[override]  # noqa: ARG002
            return [0.0] * repeat

    data = {(10, "a"): (10, "a"), (1000, "a"): (1000, "a")}
    timer = StubTimer(lambda d: sum(range(d[0])), test_data=data)
    timer.fit_strata("auto", skip_if=lambda params: False)  # noqa: ARG005

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        for _ in range(3):
            timer.run(time_per_candidate=0.01, stratify="auto", skip_if=lambda params: False)  # noqa: ARG005

    reuse_warnings = [w for w in caught if "Reusing strata" in str(w.message)]
    assert len(reuse_warnings) == 1  # one-shot guard, not once per run


def test_autonumber_generates_each_variant_once_across_rounds():
    # Escalating autorange rounds must reuse materialized data, not regenerate an (expensive) variant every round.
    import logging
    from functools import partial
    from timeit import Timer

    from rics.performance._autonumber import autonumber
    from rics.performance._generated_data import GeneratedData

    generated: list[int] = []

    def make(n: int) -> int:
        generated.append(n)
        return n

    data = GeneratedData(make, [(2,)], None, logging.getLogger("test"))

    autonumber(
        lambda d: d,  # a no-op, so the 1ms budget is only met after many autorange rounds
        "noop",
        data,
        {(2,)},
        time_allocation=1e-3,
        skip_if=None,
        make_timer=lambda f, d: Timer(partial(f, d)),
    )

    assert generated == [2]  # generated once, not once per round


def test_autonumber_never_holds_more_than_one_variant_in_memory():
    # Memory-pressure guarantee: a multi-variant stratum must be regenerated per round, never accumulated, so the
    # number of *reachable* datasets stays O(1) regardless of stratum size. An O(n) implementation (materializing
    # the whole stratum) would keep all four reachable at once. A stand-in timer is used deliberately: timeit.Timer
    # keeps the dataset in a reference cycle, deferring release to the GC and masking true (reachable) retention.
    import logging
    from timeit import Timer

    from rics.performance._autonumber import autonumber
    from rics.performance._generated_data import GeneratedData

    class Tracked:
        live = 0
        peak = 0

        def __init__(self) -> None:
            Tracked.live += 1
            Tracked.peak = max(Tracked.peak, Tracked.live)

        def __del__(self) -> None:
            Tracked.live -= 1

    class _ScaledTimer:
        # Reports time proportional to `number` (forcing several autorange rounds); retains nothing across calls.
        def timeit(self, number: int) -> float:
            return number * 1e-4

    def make_timer(func: object, data: object) -> Timer:  # noqa: ARG001
        return _ScaledTimer()  # type: ignore[return-value]

    cases = [(1,), (2,), (3,), (4,)]
    data = GeneratedData(lambda n: Tracked(), cases, None, logging.getLogger("test"))  # noqa: ARG005

    autonumber(
        lambda d: d,
        "noop",
        data,
        set(cases),  # one multi-variant stratum
        time_allocation=3e-3,  # met around number=10 -> several rounds, each regenerating all four variants
        skip_if=None,
        make_timer=make_timer,
    )

    assert Tracked.peak <= 2  # bounded (transient gen overlap), not proportional to the 4-variant stratum
