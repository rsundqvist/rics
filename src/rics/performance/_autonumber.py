"""Standalone ``timeit.Timer.autorange``-style calibration of the iteration ``number``."""

import logging
from collections.abc import Callable, Collection, Hashable
from time import perf_counter
from timeit import Timer
from typing import Any, TypeAlias

from rics.misc import tname
from rics.strings import format_perf_counter

from ._generated_data import GeneratedData
from ._progress import make_progress
from ._skip_if import SkipIfFunc, SkipIfParams
from ._strata import Strata
from .types import CandFunc, DataType, Ts

_Calibration: TypeAlias = tuple[int, float | None]
"""A derived ``(number, estimated_time)``; the time is ``None`` when `number` was supplied explicitly."""
_StratumNumbers: TypeAlias = dict[Hashable, _Calibration]
"""One candidate's calibration: stratum key -> (number, estimated_time)."""
_CandidateNumbers: TypeAlias = dict[str, _StratumNumbers | None]
"""All candidates' calibration; the value is ``None`` for a candidate whose every stratum was filtered by `skip_if`."""


def compute_candidate_numbers(
    candidates: dict[str, CandFunc[DataType]],
    test_data: dict[Hashable, DataType] | GeneratedData[DataType, *Ts],
    strata: Strata,
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
        return {c: {s: (number, None) for s in strata} for c in candidates}

    logger.debug("Computing number of iterations with repeat=%i and time_allocation=%f.", repeat, time_allocation)
    start = perf_counter()

    pbar = make_progress(len(candidates) * len(strata), enabled=progress, logger=logger)

    numbers: _CandidateNumbers = {}
    for label, func in candidates.items():
        by_stratum: _StratumNumbers = {}
        for stratum, data_labels in strata.items():
            pbar.set_description(f"autorange('{label}', {'*' if stratum is None else stratum})")
            calibration = autonumber(
                func,
                label,
                test_data,
                data_labels,
                time_allocation=time_allocation,
                skip_if=skip_if,
                make_timer=make_timer,
            )
            if calibration is not None:
                by_stratum[stratum] = calibration
                logger.debug("Number for candidate=%r stratum=%r: %i (time=%f).", label, stratum, *calibration)
            pbar.update()

        if by_stratum:
            numbers[label] = by_stratum
        else:
            logger.warning(f"Discarding candidate={label!r}; skipped by {tname(skip_if)} at {time_allocation=}.")
            numbers[label] = None

    pbar.close()

    kept = {k: v for k, v in numbers.items() if v is not None}
    if kept:
        logger.info(f"Computed number for {len(kept)} candidates in {format_perf_counter(start)}: {kept}.")
    else:
        logger.warning(f"All candidates {len(numbers)} discarded by {tname(skip_if)} at {time_allocation=}.")

    return numbers


def autonumber(
    func: CandFunc[DataType],
    candidate_label: str,
    test_data: "dict[Hashable, DataType] | GeneratedData[DataType, *Ts]",
    stratum_labels: Collection[Hashable],
    *,
    time_allocation: float,
    skip_if: SkipIfFunc[DataType, *Ts] | None,
    make_timer: Callable[[CandFunc[DataType], DataType], Timer],
) -> tuple[int, float] | None:
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

    # Single-entry cache so a one-variant stratum (e.g. every stratify="auto" cost probe) is generated once rather
    # than once per autorange round. We deliberately keep AT MOST ONE variant alive at a time: a multi-variant stratum
    # is regenerated each round, because the timer must never hold more than one dataset in memory at once (a hard
    # requirement for benchmarking high memory-pressure workloads).
    cache: dict[Hashable, DataType] = {}

    def data_for(data_label_: Hashable) -> DataType:
        if data_label_ not in cache:
            cache.clear()  # Drop the previous variant before materializing the next.
            cache[data_label_] = _data_for(test_data, data_label_)
        return cache[data_label_]

    i = 1
    while True:
        for j in 1, 2, 3, 5:
            number = i * j

            total_time_taken = 0.0
            all_skipped = True
            for data_label in stratum_labels:
                data = data_for(data_label)
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


def _data_for(
    test_data: "dict[Hashable, DataType] | GeneratedData[DataType, *Ts]",
    label: Hashable,
) -> DataType:
    """Materialize a single label's data on demand.

    Calibration probes one stratum at a time and resolves data per-label here (rather than scanning the whole dataset
    and filtering), so only the stratum's variants are generated. The caller caches the single most-recent variant, so
    a one-variant stratum is generated once rather than once per autorange round -- while never holding more than one
    dataset in memory at a time (multi-variant strata are regenerated each round).
    """
    if isinstance(test_data, GeneratedData):
        return test_data.generate(label)  # type: ignore[arg-type]  # a generated label *is* its case tuple
    return test_data[label]
