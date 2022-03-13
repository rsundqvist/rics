import logging
import warnings
from timeit import Timer
from typing import Any, Callable, Collection, Dict, List, Optional, Union

from rics.utility.misc import tname
from rics.utility.perf._format_perf_counter import format_perf_counter

LOGGER = logging.getLogger(__package__)

CandFunc = Callable[[Any], None]
ResultsDict = Dict[str, Dict[str, List[float]]]


class MultiCaseTimer:
    """Performance testing implementation for multiple candidates and data sets.

    Args:
        candidate_method: A single method, collection of method or a dict {label: function} of candidates.
        test_data: A single datum or a dict {label: data} to evaluate candidates on.
        sanity_check: If True, verify total expected runtime.
    """

    EXPECTED_RUNTIME_WARNING_LIMIT = 3 * 60 * 60
    """Warn of long runtimes above this limit (3 hours)."""

    def __init__(
        self,
        candidate_method: Union[CandFunc, Collection[CandFunc], Dict[str, CandFunc]],
        test_data: Union[Any, Dict[str, Any]],
        sanity_check: bool = True,
    ) -> None:
        self._candidates = _process_candidates(candidate_method)

        self._data = test_data if isinstance(test_data, dict) else _process_single_test_datum(test_data)
        self._check = sanity_check

    def run(
        self,
        time_per_candidate: float = 6.0,
        repeat: int = 5,
        number: int = None,
        max_expected_runtime: int = 604_800,
    ) -> ResultsDict:
        """Run for all cases.

        Note that the test case variant data isn't included in the expected runtime computation, so increasing the
        amount of test data variants (at initialization) will reduce the amount of times each candidate is evaluated.

        Args:
            time_per_candidate: Desired runtime for each repetition per candidate label. Ignored if `number` is set.
            repeat: Number of times to repeat for all candidates per data label.
            number: Number of times to execute each test case, per repetition. None=base on `per_case_time_allocation`.
            max_expected_runtime: Maximum expected runtime to allow before throwing an exception. None=disabled. Default
                is one week (604 800 seconds).

        Examples:
            If `repeat=5` and `time_per_candidate=3` for an instance with and 2 candidates, the total
            runtime will be approximately ``5 * 3 * 2 = 30`` seconds.

        Returns:
            A dict `run_results` on the form {candidate_label, {data_label, [runtime..]}}.

        Raises:
            ValueError: If the total expected runtime exceeds `max_expected_runtime`.

        Notes:
            * Precomputed runtime is inaccurate for functions where a single call are longer than `time_per_candidate`.
            * By default, this function reports averages of all runs (repetition), as opposed to the built-in timeit
              which reports only the best result (in non-verbose mode).

        See Also:
            The :py:class:`timeit.Timer` class which this implementation depends on.
        """
        per_candidate_number = self._compute_number_of_iterations(number, time_per_candidate)
        if self._check and number is None:
            self._sanity_check(repeat, time_per_candidate, max_expected_runtime)

        run_results = {}
        for candidate_label, func in self._candidates.items():
            candidate_number = per_candidate_number[candidate_label]
            candidate_results: Dict[str, List[float]] = {}
            LOGGER.debug("Run candidate '%s' %dx%d times...", candidate_label, repeat, candidate_number)
            for data_label, test_data in self._data.items():
                raw_timings = Timer(lambda: func(test_data)).repeat(repeat, candidate_number)
                candidate_results[data_label] = [dt / candidate_number for dt in raw_timings]

            _cache_warning(candidate_results, candidate_label)
            run_results[candidate_label] = candidate_results

        return run_results

    def _compute_number_of_iterations(self, number: Optional[int], time_allocation: float) -> Dict[str, int]:
        if isinstance(number, int):
            ans = {case: number for case in self._data}
        else:
            ans = {}
            for candidate_label, candidate_func in self._candidates.items():

                def _run_all() -> None:
                    for data in self._data.values():
                        candidate_func(data)

                number, time_taken = Timer(_run_all).autorange()
                ans[candidate_label] = max(2, int(number * time_allocation / time_taken))

        return ans

    def _sanity_check(self, repeat: int, time_allocation: float, max_expected_runtime: Optional[float]) -> None:
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


def _process_candidates(candidates: Union[CandFunc, Collection[CandFunc], Dict[str, CandFunc]]) -> Dict[str, CandFunc]:
    if isinstance(candidates, dict):
        return candidates
    if callable(candidates):
        return {tname(candidates): candidates}

    return {tname(c): c for c in candidates}


def _process_single_test_datum(test_data: Any) -> Dict[str, Any]:
    s = repr(test_data)
    key = f"{s[:32]}..." if len(s) > 32 else s
    return {f"Example: '{key}'": test_data}


def _cache_warning(candidate_results: Dict[str, List[float]], candidate: str) -> None:
    # Similar to the warning that's sent by the native timeit module
    for label, timings in candidate_results.items():
        best = min(timings)
        worst = max(timings)
        if worst >= best * 4:
            warnings.warn(
                f"The test results may be unreliable for ('{candidate}', '{label}'). The worst time ({worst} sec) was "
                f"more than four times slower than the best time ({best}). An intermediate result may be cached."
            )
