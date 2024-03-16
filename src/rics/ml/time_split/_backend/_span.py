from collections.abc import Callable
from datetime import timedelta
from typing import Literal, TypeAlias

from pandas import DatetimeIndex, Timedelta, Timestamp

from ..types import Span
from ._limits import LimitsTuple
from ._schedule import NO_LIMITS

StrictSpan: TypeAlias = int | Timedelta | Literal["all"]
SpanArgumentName = Literal["before", "after"]
FuncType = Callable[[int], Timestamp | None]


class InvalidSpanError(ValueError):
    """Raised when offsets values for 'before' and 'after' arguments are invalid."""

    def __init__(
        self,
        span: Span,
        *,
        name: SpanArgumentName,
        reason: str = "must be greater than zero",
    ) -> None:
        super().__init__(f"Bad '{name}'-argument; offset {span!r} {reason}.")


def _to_timedelta(span: str | timedelta | Timedelta, *, name: SpanArgumentName) -> Timedelta:
    retval = Timedelta(span)
    if retval <= Timedelta(0):
        raise InvalidSpanError(span, name=name)
    return retval


def to_strict_span(span: Span, *, name: SpanArgumentName) -> StrictSpan:
    """Convert `span` to a strict span.

    Args:
        span: User span.
        name: Name of user input. User for error reporting.

    Returns:
        A valid span with reduced types.

    Raises:
        TypeError: For bad `span` types.
        InvalidSpanError: For invalid `span` arguments.

    """
    if span == "all":
        return "all"

    if isinstance(span, (str, timedelta, Timedelta)):
        return _to_timedelta(span, name=name)

    if span is False or isinstance(span, (int, float)):
        retval = int(span)
        if retval <= 0:
            raise InvalidSpanError(retval, name=name)
        return retval

    raise TypeError(f"cannot parse '{name}'-argument of type {type(span).__name__}: {span!r}.")


class OffsetCalculator:
    """Utility class for computing before/after offsets from the `schedule`."""

    def __init__(
        self,
        span: Span,
        schedule: DatetimeIndex,
        limits: LimitsTuple,
        *,
        name: SpanArgumentName,
    ) -> None:
        span = to_strict_span(span, name=name)
        is_before = name == "before"

        self.func: FuncType
        if span == "all":
            if limits == NO_LIMITS:
                raise InvalidSpanError(
                    span,
                    name=name,
                    reason="requires available data to bound the schedule",
                )
            self.func = self._make_all(is_before, limits)
        elif isinstance(span, int):
            self.func = self._make_int(is_before, span, schedule)
        else:  # Timedelta
            self.func = self._make_timedelta(is_before, span, schedule)

    @staticmethod
    def _make_all(is_before: bool, limits: LimitsTuple) -> FuncType:
        retval = Timestamp(limits[0 if is_before else 1])

        def func(_: int) -> Timestamp | None:
            return retval

        return func

    @staticmethod
    def _make_int(is_before: bool, offset: int, schedule: DatetimeIndex) -> FuncType:
        def func(i: int) -> Timestamp | None:
            i = i - offset if is_before else i + offset
            if 0 <= i < len(schedule):
                return schedule[i]
            else:
                return None

        return func

    @staticmethod
    def _make_timedelta(is_before: bool, offset: Timedelta, schedule: DatetimeIndex) -> FuncType:
        if is_before:
            schedule = schedule - offset
        else:
            schedule = schedule + offset

        def func(i: int) -> Timestamp | None:
            return schedule[i]

        return func

    def __call__(self, i: int) -> Timestamp | None:
        """Get start/end timestamp."""
        return self.func(i)
