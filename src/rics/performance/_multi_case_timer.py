import logging
import warnings
from collections.abc import Collection, Hashable, Mapping
from timeit import Timer
from typing import Any, Generic, TypeAlias

from rics.strings import format_seconds as fmt_time

from ..misc import tname
from .types import CandFunc, DataType, ResultsDict

CandidateMethodArg: TypeAlias = dict[str, CandFunc[DataType]] | Collection[CandFunc[DataType]] | CandFunc[DataType]
TestDataArg: TypeAlias = dict[Hashable, DataType] | Collection[DataType]


class MultiCaseTimer(Generic[DataType]):
    """Performance testing implementation for multiple candidates and data sets.

    For non-dict inputs, string labels will be generated automatically.

    Args:
        candidate_method: A dict ``{label: function}``. Alternatively, you may pass a collection of functions or a
            single function.
        test_data: A ``{label: data}`` to evaluate candidates on. Alternatively, you may pass a list of data.

    """

    def __init__(self, candidate_method: CandidateMethodArg[DataType], test_data: TestDataArg[DataType]) -> None:
        self._candidates = self._process_candidates(candidate_method)
        if not self._candidates:
            raise ValueError("No candidates given.")  # pragma: no cover

        self._data = test_data if isinstance(test_data, dict) else self._dict_from_collection(test_data)
        if not self._data:
            raise ValueError("No case data given.")  # pragma: no cover

    def run(
        self,
        time_per_candidate: float = 6.0,
        repeat: int = 5,
        number: int | None = None,
        progress: bool = False,
    ) -> ResultsDict:
        """Run for all cases.

        Note that the test case variant data isn't included in the expected runtime computation, so increasing the
        amount of test data variants (at initialization) will reduce the amount of times each candidate is evaluated.

        Args:
            time_per_candidate: Desired runtime for each repetition per candidate label. Ignored if `number` is set.
            repeat: Number of times to repeat for all candidates per data label.
            number: Number of times to execute each test case, per repetition. Compute based on
                `per_case_time_allocation` if ``None``.
            progress: If ``True``, display a progress bar. Required ``tqdm``.

        Examples:
            If `repeat=5` and `time_per_candidate=3` for an instance with and 2 candidates, the total
            runtime will be approximately ``5 * 3 * 2 = 30`` seconds.

        Returns:
            A dict `run_results` on the form ``{candidate_label: {data_label: [runtime, ...]}}``.

        Raises:
            ValueError: If the total expected runtime exceeds `max_expected_runtime`.

        Notes:
            * Precomputed runtime is inaccurate for functions where a single call are longer than `time_per_candidate`.

        See Also:
            The :py:class:`timeit.Timer` class which this implementation depends on.

        """
        per_candidate_number = self._compute_number_of_iterations(number, repeat, time_per_candidate)

        total = len(self._candidates) * len(self._data)
        if progress:
            from tqdm.auto import tqdm

            pbar = tqdm(total=total)
        else:
            pbar = None

        i = 0
        logger = logging.getLogger(__package__)
        run_results: ResultsDict = {}
        for candidate_label, func in self._candidates.items():
            candidate_number = per_candidate_number[candidate_label]
            candidate_results: dict[Hashable, list[float]] = {}

            logger.info(f"Evaluate candidate {candidate_label!r} {repeat}x{candidate_number} times per datum..")
            for data_label, test_data in self._data.items():
                if pbar:
                    pbar.desc = f"{candidate_label}: {data_label}"
                    pbar.refresh()
                i += 1
                logger.debug(f"Start evaluating combination {i}/{total}: {candidate_label!r} @ {data_label!r}.")

                raw_timings = self._get_raw_timings(func, test_data, candidate_number, repeat)
                best, worst = min(raw_timings), max(raw_timings)
                candidate_results[data_label] = [dt / candidate_number for dt in raw_timings]
                if worst >= best * 4:
                    t = (candidate_label, data_label)
                    warnings.warn(
                        f"The test results may be unreliable for {t}. The worst time {fmt_time(worst)} "
                        f"was ~{worst / best:.1f} times slower than the best time ({fmt_time(best)}).",
                        UserWarning,
                        stacklevel=1,
                    )
                if pbar:
                    pbar.update(1)
            run_results[candidate_label] = candidate_results

        return run_results

    @staticmethod
    def _get_raw_timings(func: CandFunc[DataType], test_data: DataType, repeat: int, number: int) -> list[float]:
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

    @staticmethod
    def _process_candidates(
        candidates: CandFunc[DataType] | Collection[CandFunc[DataType]] | Mapping[str, CandFunc[DataType]],
    ) -> dict[str, CandFunc[DataType]]:
        if isinstance(candidates, dict):
            return candidates
        if callable(candidates):
            return {tname(candidates): candidates}

        def make_label(a: Any) -> str:
            name = tname(a)
            return name[len("candidate_") :] if name.startswith("candidate_") else name

        labeled_candidates = {make_label(c): c for c in candidates}
        if len(labeled_candidates) != len(candidates):
            raise ValueError(
                f"Derived names for input {candidates=} are not unique. Use a dict to assign candidate names."
            )
        return labeled_candidates  # type: ignore[return-value]

    @staticmethod
    def _dict_from_collection(test_data: Collection[DataType]) -> dict[Hashable, DataType]:
        result: dict[Hashable, DataType] = {}
        for data in test_data:
            s = str(data)
            key = f"{s[:29]}..." if len(s) > 32 else s  # noqa: PLR2004
            result[f"Sample data: '{key}'"] = data
        return result
