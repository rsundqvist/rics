import logging
from typing import Iterable, List, NamedTuple, Optional, Tuple, Union

from pandas import Timedelta, Timestamp

from rics.misc import get_public_module

from ..settings import auto_flex as settings
from ..types import Flex, TimedeltaTypes

LimitsTuple = Tuple[Timestamp, Timestamp]
LevelTuple = Tuple[TimedeltaTypes, TimedeltaTypes, TimedeltaTypes]


class _TimedeltaTuple(NamedTuple):
    start_at: Timedelta
    round_to: Timedelta
    tolerance: Timedelta


def expand_limits(limits: LimitsTuple, *, flex: Union[Flex, LevelTuple, Iterable[LevelTuple]]) -> LimitsTuple:
    """Derive the `"real"` bounds of `limits`."""
    if limits[0] >= limits[1]:
        raise ValueError(f"Bad limits. Expected limits[1] > limits[0], but got {limits=}.")

    if flex is False:
        return limits

    if flex is True or flex == "auto":
        return _from_levels(limits)

    if isinstance(flex, str):
        round_to, _, tolerance = flex.partition("<")
        level = _make_level(None, round_to=round_to.strip(), tolerance=tolerance.strip())
        return _apply(limits, level=level)
    if isinstance(flex, tuple):
        return _from_levels(limits, levels=[_make_level(*flex)])

    return _from_levels(limits, levels=(_make_level(*t) for t in flex))


def _from_levels(limits: LimitsTuple, *, levels: Iterable[_TimedeltaTuple] = None) -> LimitsTuple:
    if levels is None:
        levels = _levels_from_settings()
    else:
        levels = sorted(levels, reverse=True, key=lambda l: l[0])

    lo, hi = limits
    diff = hi - lo

    for level in levels:
        start_at, round_to, tolerance = level
        if diff >= start_at:
            return _apply(limits, level=level)

    return limits


def _apply(limits: LimitsTuple, *, level: _TimedeltaTuple) -> LimitsTuple:
    lo, hi = limits

    lo_floor = lo.floor(level.round_to)
    if abs(lo_floor - lo) > level.tolerance:
        return limits

    hi_ceil = hi.ceil(level.round_to)
    if abs(hi_ceil - hi) > level.tolerance:
        return limits

    if settings.SANITY_CHECK:
        if lo.round(level.round_to) != lo_floor:
            return limits
        if hi.round(level.round_to) != hi_ceil:
            return limits

    retval = (lo_floor, hi_ceil)

    logger = logging.getLogger(get_public_module(_apply)).getChild("flex")
    if logger.isEnabledFor(logging.INFO) and limits != retval:
        from .._frontend._to_string import _PrettyTimestamp

        logger.info(
            f"Available data limits have been expanded:\n"
            f"  Start: {lo} -> {_PrettyTimestamp(lo_floor).auto if lo != lo_floor else '<no change>'}\n"
            f"    End: {hi} -> {_PrettyTimestamp(hi_ceil).auto if hi != hi_ceil else '<no change>'}"
        )
    return retval


def _levels_from_settings() -> List[_TimedeltaTuple]:
    day, hour = _make_level(*settings.day), _make_level(*settings.hour)
    if day.round_to != Timedelta(days=1):
        raise ValueError(f"Invalid settings: {settings.day=} must have round_to=1 day.")
    if hour.round_to != Timedelta(hours=1):
        raise ValueError(f"Invalid settings: {settings.hour=} must have round_to=1 hour.")
    return [day, hour]


def _make_level(
    start_at: Optional[TimedeltaTypes],
    round_to: TimedeltaTypes,
    tolerance: TimedeltaTypes,
) -> _TimedeltaTuple:
    start_at = Timedelta(start_at)  # Will be NaT if None, making all ifs False.
    if start_at <= Timedelta(0):
        raise ValueError(f"Bad {start_at=}; must be non-negative.")

    try:
        round_to = Timedelta(1, unit=round_to)
    except ValueError as e:
        raise ValueError(f"Got {round_to=}, which is not a valid frequency.") from e

    tolerance = Timedelta(tolerance)
    if tolerance <= Timedelta(0):
        raise ValueError(f"Bad {tolerance=}; must be non-negative.")

    if start_at < round_to:
        raise ValueError(f"{start_at=} < {round_to=}")
    if round_to < tolerance:
        raise ValueError(f"{round_to=} < {tolerance=}")
    return _TimedeltaTuple(start_at, round_to, tolerance)
