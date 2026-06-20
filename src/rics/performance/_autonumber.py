"""Standalone ``timeit.Timer.autorange``-style calibration of the iteration ``number``."""

import functools
import logging
from collections.abc import Hashable
from time import perf_counter
from timeit import Timer
from typing import Any, TypeAlias

from rics.strings import format_perf_counter

from ._generated_data import GeneratedData
from .types import CandFunc, DataType, Ts

_CandidateNumbers: TypeAlias = "dict[str, tuple[int, float | None]]"
"""One ``(number, estimated_time)`` per candidate; the time is ``None`` when `number` was supplied explicitly."""


def compute_candidate_numbers(
    candidates: dict[str, CandFunc[DataType]],
    test_data: "dict[Hashable, DataType] | GeneratedData[DataType, *Ts]",
    *,
    number: int | None,
    repeat: int,
    time_allocation: float,
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

        candidate_numbers[label] = calibration = autonumber(func, test_data, time_allocation=time_allocation)
        logger.debug("Candidate number for candidate=%r: %i (time=%f).", label, *calibration)
        if pbar:
            pbar.update()

    if pbar:
        pbar.clear()

    logger.info(
        f"Computed shared number for {len(candidate_numbers)} candidates in {format_perf_counter(start)}: "
        f"{candidate_numbers}."
    )

    return candidate_numbers


def autonumber(
    func: CandFunc[DataType],
    test_data: "dict[Hashable, DataType] | GeneratedData[DataType, *Ts]",
    *,
    time_allocation: float,
) -> tuple[int, float]:
    """Based on ``timeit.Timer.autorange()``."""
    i = 1
    while True:
        for j in 1, 2, 3, 5:
            number = i * j

            total_time_taken = 0.0
            for _, data in test_data.items():
                total_time_taken += Timer(functools.partial(func, data)).timeit(number)

            if total_time_taken >= time_allocation:
                if total_time_taken > 1:
                    total_time_taken = round(total_time_taken, 2)
                return number, total_time_taken
        i *= 10
