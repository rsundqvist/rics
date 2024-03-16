from typing import Any, Literal, overload

from pandas import Timestamp

from ..settings import log_split_progress
from ..types import DatetimeSplitBounds, DatetimeTypes


@overload
def to_string(
    bounds: DatetimeTypes,
    __ignored0: DatetimeTypes,
    __ignored1: DatetimeTypes,
    /,
    *,
    format: str | None = None,
) -> str: ...


@overload
def to_string(
    start: tuple[DatetimeTypes, DatetimeTypes, DatetimeTypes],
    mid: Literal[None] = None,
    end: Literal[None] = None,
    /,
    *,
    format: str | None = None,
) -> str: ...


def to_string(
    bounds: (DatetimeTypes | DatetimeSplitBounds | tuple[DatetimeTypes, DatetimeTypes, DatetimeTypes]),
    mid: DatetimeTypes | None = None,
    end: DatetimeTypes | None = None,
    /,
    *,
    format: str | None = None,
) -> str:
    """Pretty-print a fold.

    .. code-block:: python
       :caption: Sample output.

       ('2021-12-30' <= [schedule: '2022-01-04' (Tuesday)] < '2022-01-04 18:00:00')

    Args:
        bounds: A fold tuple ``(start, mid, end)``, or just `start` (followed by `mid` and `end`).
        mid: Datetime-like. Must be ``None`` when `bounds` is a tuple.
        end: Datetime-like. Must be ``None`` when `bounds` is a tuple.
        format: A custom format to use. Use :attr:`~.settings.log_split_progress.FOLD_FORMAT` if ``None``, but note that
            only the `start`, `mid` and `end` keys are available to this function.

    Returns:
        Formatted bounds string.

    Raises:
        TypeError: If an incorrect number of timestamps are given.

    """
    if isinstance(bounds, tuple):
        if not (mid is None and end is None):
            raise TypeError(f"Too many arguments: {(bounds, mid, end)}.")
        start, mid, end = bounds
    else:
        if mid is None or end is None:
            raise TypeError(f"Too few arguments: {(bounds, mid, end)}.")
        start = bounds

    return (log_split_progress.FOLD_FORMAT if format is None else format).format(
        start=_PrettyTimestamp(start),
        mid=_PrettyTimestamp(mid),
        end=_PrettyTimestamp(end),
    )


class _PrettyTimestamp:
    def __init__(self, raw: DatetimeTypes) -> None:
        self.timestamp = Timestamp(raw)
        self._auto: str | None = None

    def __getattr__(self, name: str) -> Any:
        return getattr(self.timestamp, name)

    def __str__(self) -> str:
        return str(self.timestamp)

    def __repr__(self) -> str:
        return repr(self.timestamp)

    def __format__(self, format_spec: str) -> str:
        return format(self.timestamp, format_spec)

    @property
    def auto(self) -> str:
        if self._auto is None:
            timestamp = self.timestamp.round("s")
            format_spec = (
                log_split_progress.AUTO_DATE_FORMAT
                if timestamp.normalize() == timestamp
                else log_split_progress.AUTO_DATETIME_FORMAT
            )
            self._auto = format(timestamp, format_spec)
        return self._auto
