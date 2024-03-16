from collections.abc import Iterable
from itertools import starmap
from typing import NamedTuple

from pandas import Timedelta, Timestamp

from ..settings import auto_flex
from ..types import Flex, TimedeltaTypes

LimitsTuple = tuple[Timestamp, Timestamp]
LevelTuple = tuple[TimedeltaTypes, TimedeltaTypes, TimedeltaTypes]


class _TimedeltaTuple(NamedTuple):
    start_at: Timedelta
    round_to: Timedelta
    tolerance: Timedelta


def expand_limits(limits: LimitsTuple, *, flex: Flex | LevelTuple | Iterable[LevelTuple] = "auto") -> LimitsTuple:
    """Derive the `"real"` bounds of `limits`.

    Args:
        limits: A tuple ``(lo, hi)`` of timestamps.
        flex: Flex arguments as described in the :ref:`User guide`. Also supports level-tuples
            ``[(start_at, round_to, tolerance)...]``. Passing ``flex=[settings.auto_flex.day, settings.auto_flex.hour]``
            is equivalent to ``flex='auto'``.

    Returns:
        Limits rounded according to the `flex`-argument.

    Raises:
        ValueError: For invalid limits.

    Examples:
        >>> from pandas import Timestamp
        >>> limits = Timestamp("2019-05-11"), Timestamp("2019-05-11 22:05:30")

        Basic usage.

        >>> expand_limits(limits, flex="d")
        (Timestamp('2019-05-11 00:00:00'), Timestamp('2019-05-12 00:00:00'))

        You may specify a maximum "distance" that limits may be expanded.

        >>> expand_limits(limits, flex="d<1h")
        (Timestamp('2019-05-11 00:00:00'), Timestamp('2019-05-11 22:05:30'))

        Limits will never be rounded in the "wrong" direction...

        >>> limits = Timestamp("2019-05-11"), Timestamp("2019-05-11 11:05:30")
        >>> expand_limits(limits, flex="d")
        (Timestamp('2019-05-11 00:00:00'), Timestamp('2019-05-11 11:05:30'))

        ...even if you make the tolerance large enough.

        >>> expand_limits(limits, flex="d<14h")
        (Timestamp('2019-05-11 00:00:00'), Timestamp('2019-05-11 11:05:30'))

    """
    if limits[0] >= limits[1]:
        msg = f"Bad limits. Expected limits[1] > limits[0], but got {limits=}."
        raise ValueError(msg)

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

    return _from_levels(limits, levels=starmap(_make_level, flex))


def _from_levels(limits: LimitsTuple, *, levels: Iterable[_TimedeltaTuple] | None = None) -> LimitsTuple:
    if levels is None:
        levels = _levels_from_settings()
    else:
        levels = sorted(levels, reverse=True, key=lambda level: level[0])

    lo, hi = limits
    diff = hi - lo

    for level in levels:
        start_at, _round_to, _tolerance = level
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

    if auto_flex.SANITY_CHECK:
        if lo.round(level.round_to) != lo_floor:
            return limits
        if hi.round(level.round_to) != hi_ceil:
            return limits

    return lo_floor, hi_ceil


def _levels_from_settings() -> list[_TimedeltaTuple]:
    day, hour = _make_level(*auto_flex.day), _make_level(*auto_flex.hour)
    if day.round_to != Timedelta(days=1):
        msg = f"Invalid settings: {auto_flex.day=} must have round_to=1 day."
        raise ValueError(msg)
    if hour.round_to != Timedelta(hours=1):
        msg = f"Invalid settings: {auto_flex.hour=} must have round_to=1 hour."
        raise ValueError(msg)
    return [day, hour]


def _make_level(
    start_at: TimedeltaTypes | None,
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
