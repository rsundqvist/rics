import logging
import warnings
from timeit import Timer
from typing import Any, Callable, Collection, Dict, List, Optional, Union

from rics.performance._format_perf_counter import format_perf_counter
from rics.performance._format_perf_counter import format_seconds as fmt_time
from rics.utility.misc import tname

LOGGER = logging.getLogger(__package__)

CandFunc = Callable[[Any], None]
ResultsDict = Dict[str, Dict[str, List[float]]]


class MultiCaseTimer:
    """Performance testing implementation for multiple candidates and data sets.

    Args:
        candidate_method: A single method, collection of method or a dict {label: function} of candidates.
        test_data: A single datum or a dict ``{label: data}`` to evaluate candidates on.
        sanity_check: If ``True``, verify total expected runtime.
    """

    EXPECTED_RUNTIME_WARNING_LIMIT = 4 * 60 * 60
    """Warn of long runtimes above this limit (4 hours)."""
    EXPECTED_RUNTIME_ERROR_LIMIT: int = 6 * EXPECTED_RUNTIME_WARNING_LIMIT
    """Raise an exceptions above this limit (six times the ``EXPECTED_RUNTIME_WARNING_LIMIT``)."""

    def __init__(
        self,
        candidate_method: Union[CandFunc, Collection[CandFunc], Dict[str, CandFunc]],
        test_data: Union[Any, Dict[str, Any]],
        sanity_check: bool = True,
    ) -> None:
        self._candidates = _process_candidates(candidate_method)
        if not self._candidates:  # pragma: no cover
            raise ValueError("No candidates given.")

        self._data = test_data if isinstance(test_data, dict) else _process_single_test_datum(test_data)
        if not self._data:  # pragma: no cover
            raise ValueError("No case data given.")
        self._check = sanity_check

    def run(
        self,
        time_per_candidate: float = 6.0,
        repeat: int = 5,
        number: int = None,
    ) -> ResultsDict:
        """Run for all cases.

        Note that the test case variant data isn't included in the expected runtime computation, so increasing the
        amount of test data variants (at initialization) will reduce the amount of times each candidate is evaluated.

        Args:
            time_per_candidate: Desired runtime for each repetition per candidate label. Ignored if `number` is set.
            repeat: Number of times to repeat for all candidates per data label.
            number: Number of times to execute each test case, per repetition. Compute based on
                `per_case_time_allocation` if ``None``.

        Examples:
            If `repeat=5` and `time_per_candidate=3` for an instance with and 2 candidates, the total
            runtime will be approximately ``5 * 3 * 2 = 30`` seconds.

        Returns:
            A dict `run_results` on the form ``{candidate_label: {data_label: [runtime..]}}``.

        Raises:
            ValueError: If the total expected runtime exceeds `max_expected_runtime`.

        Notes:
            * Precomputed runtime is inaccurate for functions where a single call are longer than `time_per_candidate`.

        See Also:
            The :py:class:`timeit.Timer` class which this implementation depends on.
        """
        per_candidate_number = self._compute_number_of_iterations(number, time_per_candidate)
        if self._check and number is None:  # pragma: no cover
            self._sanity_check(repeat, time_per_candidate, self.EXPECTED_RUNTIME_ERROR_LIMIT)

        run_results = {}
        for candidate_label, func in self._candidates.items():
            candidate_number = per_candidate_number[candidate_label]
            candidate_results: Dict[str, List[float]] = {}
            LOGGER.info("Evaluate candidate '%s' %dx%d times...", candidate_label, repeat, candidate_number)
            for data_label, test_data in self._data.items():
                raw_timings = Timer(lambda: func(test_data)).repeat(repeat, candidate_number)  # noqa: B023
                best, worst = min(raw_timings), max(raw_timings)
                candidate_results[data_label] = [dt / candidate_number for dt in raw_timings]
                if worst >= best * 4:  # pragma: no cover
                    t = (candidate_label, data_label)
                    warnings.warn(
                        f"The test results may be unreliable for {t}. The worst time {fmt_time(worst)} "
                        f"was ~{worst / best:.1f} times slower than the best time ({fmt_time(best)}).",
                        UserWarning,
                        stacklevel=0,
                    )
            run_results[candidate_label] = candidate_results

        return run_results

    def _compute_number_of_iterations(
        self, number: Optional[int], time_allocation: float
    ) -> Dict[str, int]:  # pragma: no cover
        if isinstance(number, int):
            ans = {case: number for case in self._data}
        else:
            ans = {}
            for candidate_label, candidate_func in self._candidates.items():

                def _run_all() -> None:
                    for data in self._data.values():
                        candidate_func(data)  # noqa: B023

                number, time_taken = Timer(_run_all).autorange()
                ans[candidate_label] = max(2, int(number * time_allocation / time_taken))

        return ans

    def _sanity_check(
        self, repeat: int, time_allocation: float, max_expected_runtime: Optional[float]
    ) -> None:  # pragma: no cover
        expected_runtime = len(self._candidates) * repeat * time_allocation

        ert_nice = format_perf_counter(0, expected_runtime)
        if max_expected_runtime is not None and expected_runtime > self.EXPECTED_RUNTIME_WARNING_LIMIT:
            warnings.warn(f"Long total expected runtime: {ert_nice}")

        if max_expected_runtime is not None and expected_runtime > max_expected_runtime:
            limit = format_perf_counter(0, max_expected_runtime)
            raise ValueError(
                f"Long expected runtime: {ert_nice} > limit={limit}. Increase 'max_expected_runtime' or"
                " set it to None to allow."
            )

        LOGGER.info(f"Expected total runtime: {ert_nice}.")


def _process_candidates(
    candidates: Union[CandFunc, Collection[CandFunc], Dict[str, CandFunc]]
) -> Dict[str, CandFunc]:  # pragma: no cover
    if isinstance(candidates, dict):
        return candidates
    if callable(candidates):
        return {tname(candidates): candidates}

    return {tname(c): c for c in candidates}


def _process_single_test_datum(test_data: Any) -> Dict[str, Any]:  # pragma: no cover
    s = repr(test_data)
    key = f"{s[:32]}..." if len(s) > 32 else s
    return {f"Example: '{key}'": test_data}
