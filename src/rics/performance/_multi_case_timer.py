import logging
import warnings
from collections.abc import Callable, Collection, Mapping
from timeit import Timer
from typing import Any

from ..misc import tname
from ._format_perf_counter import format_seconds as fmt_time

LOGGER = logging.getLogger(__package__)

DataType = Any
CandFunc = Callable[[DataType], None]
ResultsDict = dict[str, dict[str, list[float]]]


class MultiCaseTimer:
    """Performance testing implementation for multiple candidates and data sets.

    Args:
        candidate_method: A single method, collection of method or a dict {label: function} of candidates.
        test_data: A single datum or a dict ``{label: data}`` to evaluate candidates on.

    """

    def __init__(
        self,
        candidate_method: CandFunc | Collection[CandFunc] | Mapping[str, CandFunc],
        test_data: DataType | Mapping[str, DataType],
    ) -> None:
        self._candidates = _process_candidates(candidate_method)
        if not self._candidates:
            raise ValueError("No candidates given.")  # pragma: no cover

        self._data = test_data if isinstance(test_data, dict) else _process_single_test_datum(test_data)
        if not self._data:
            raise ValueError("No case data given.")  # pragma: no cover

    def run(
        self,
        time_per_candidate: float = 6.0,
        repeat: int = 5,
        number: int | None = None,
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
        per_candidate_number = self._compute_number_of_iterations(number, repeat, time_per_candidate)

        run_results = {}
        for candidate_label, func in self._candidates.items():
            candidate_number = per_candidate_number[candidate_label]
            candidate_results: dict[str, list[float]] = {}
            LOGGER.info(f"Evaluate candidate {candidate_label!r} {repeat}x{candidate_number} times..")
            for data_label, test_data in self._data.items():
                raw_timings = self._get_raw_timings(func, test_data, candidate_number, repeat)
                best, worst = min(raw_timings), max(raw_timings)
                candidate_results[data_label] = [dt / candidate_number for dt in raw_timings]
                if worst >= best * 4:
                    t = (candidate_label, data_label)
                    warnings.warn(
                        f"The test results may be unreliable for {t}. The worst time {fmt_time(worst)} "
                        f"was ~{worst / best:.1f} times slower than the best time ({fmt_time(best)}).",
                        UserWarning,
                        stacklevel=0,
                    )
            run_results[candidate_label] = candidate_results

        return run_results

    @staticmethod
    def _get_raw_timings(func: CandFunc, test_data: DataType, repeat: int, number: int) -> list[float]:
        """Exists so that it can be overridden for testing."""
        return Timer(lambda: func(test_data)).repeat(repeat, number)

    def _compute_number_of_iterations(self, number: int | None, repeat: int, time_allocation: float) -> dict[str, int]:
        if isinstance(number, int):
            retval = dict.fromkeys(self._data, number)
        else:
            retval = {}
            for candidate_label, candidate_func in self._candidates.items():

                def _run_all() -> None:
                    for data in self._data.values():
                        candidate_func(data)  # noqa: B023

                auto_number, auto_time = Timer(_run_all).autorange()
                candidate_number = int((time_allocation * auto_number) / (repeat * auto_time))
                retval[candidate_label] = max(2, candidate_number)

        return retval


def _process_candidates(
    candidates: CandFunc | Collection[CandFunc] | Mapping[str, CandFunc],
) -> dict[str, CandFunc]:
    if isinstance(candidates, dict):
        return candidates
    if callable(candidates):
        return {tname(candidates): candidates}

    def make_label(a: Any) -> str:
        name = tname(a)
        return name[len("candidate_") :] if name.startswith("candidate_") else name

    labeled_candidates = {make_label(c): c for c in candidates}
    if len(labeled_candidates) != len(candidates):
        raise ValueError(f"Derived names for input {candidates=} are not unique. Use a dict to assign candidate names.")
    return labeled_candidates  # type: ignore[return-value]


def _process_single_test_datum(test_data: DataType) -> dict[str, DataType]:
    s = repr(test_data)
    key = f"{s[:29]}..." if len(s) > 32 else s  # noqa: PLR2004
    return {f"Sample data: '{key}'": test_data}
