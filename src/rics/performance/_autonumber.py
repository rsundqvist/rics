"""Standalone ``timeit.Timer.autorange``-style calibration of the iteration ``number``."""

import logging
from collections.abc import Callable, Hashable
from time import perf_counter
from timeit import Timer
from typing import Any, TypeAlias

from rics.misc import tname
from rics.strings import format_perf_counter

from ._generated_data import GeneratedData
from ._skip_if import SkipIfFunc, SkipIfParams
from .types import CandFunc, DataType, Ts

_Calibration: TypeAlias = "tuple[int, float | None]"
"""A derived ``(number, estimated_time)``; the time is ``None`` when `number` was supplied explicitly."""
_CandidateNumbers: TypeAlias = "dict[str, _Calibration | None]"
"""One calibration per candidate; the value is ``None`` for a candidate whose every datum was filtered by `skip_if`."""


def compute_candidate_numbers(
    candidates: dict[str, CandFunc[DataType]],
    test_data: "dict[Hashable, DataType] | GeneratedData[DataType, *Ts]",
    *,
    number: int | None,
    repeat: int,
    time_allocation: float,
    skip_if: SkipIfFunc[DataType, *Ts] | None,
    make_timer: Callable[[CandFunc[DataType], DataType], Timer],
    progress: bool,
    logger: logging.Logger | logging.LoggerAdapter[Any],
) -> _CandidateNumbers:
    if isinstance(number, int):
        return {c: (number, None) for c in candidates}

    logger.debug("Computing number of iterations with repeat=%i and time_allocation=%f.", repeat, time_allocation)
    start = perf_counter()

    if progress:
        from tqdm.auto import tqdm

        pbar = tqdm(total=len(candidates))
    else:
        pbar = None

    candidate_numbers: _CandidateNumbers = {}
    for label, func in candidates.items():
        if pbar:
            pbar.desc = f"autorange('{label}')"
            pbar.refresh()

        calibration = autonumber(
            func,
            label,
            test_data,
            time_allocation=time_allocation,
            skip_if=skip_if,
            make_timer=make_timer,
        )
        candidate_numbers[label] = calibration
        if calibration is None:
            logger.warning(f"Discarding candidate={label!r}; skipped by {tname(skip_if)} at {time_allocation=}.")
        else:
            logger.debug("Candidate number for candidate=%r: %i (time=%f).", label, *calibration)
        if pbar:
            pbar.update()

    if pbar:
        pbar.clear()

    kept = {k: v for k, v in candidate_numbers.items() if v is not None}
    logger.info(
        f"Computed shared number for {len(kept)} candidates in {format_perf_counter(start)}: {kept}.",
    )

    return candidate_numbers


def autonumber(
    func: CandFunc[DataType],
    candidate_label: str,
    test_data: "dict[Hashable, DataType] | GeneratedData[DataType, *Ts]",
    *,
    time_allocation: float,
    skip_if: SkipIfFunc[DataType, *Ts] | None,
    make_timer: Callable[[CandFunc[DataType], DataType], Timer],
) -> tuple[int, float] | None:
    """Based on ``timeit.Timer.autorange()``; returns ``None`` if every datum is filtered by `skip_if`."""

    def should_skip(data_label_: Hashable, data_: DataType) -> bool:
        if skip_if is None:
            return False

        params: SkipIfParams[DataType, *Ts] = SkipIfParams(
            candidate=func,
            candidate_label=candidate_label,
            data=data_,
            data_label=data_label_,
            est_time=None,
            results_so_far={},
        )
        return skip_if(params)

    i = 1
    while True:
        for j in 1, 2, 3, 5:
            number = i * j

            total_time_taken = 0.0
            all_skipped = True
            for data_label, data in test_data.items():
                if should_skip(data_label, data):
                    continue
                all_skipped = False
                total_time_taken += make_timer(func, data).timeit(number)

            if all_skipped:
                return None

            if total_time_taken >= time_allocation:
                if total_time_taken > 1:
                    total_time_taken = round(total_time_taken, 2)
                return number, total_time_taken
        i *= 10
