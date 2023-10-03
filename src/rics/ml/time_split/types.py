"""Types related to splitting data."""

import datetime as _dt
import typing as _t

import numpy as _np
import pandas as _pd

DatetimeTypes = _t.Union[str, _pd.Timestamp, _dt.datetime, _dt.date, _np.datetime64]
"""Types that may be cast to :class:`pandas.Timestamp`."""
DatetimeIterable = _t.Iterable[DatetimeTypes]
"""Iterable that may be cast to :class:`pandas.DatetimeIndex`."""
TimedeltaTypes = _t.Union[str, _pd.Timedelta, _dt.timedelta, _np.timedelta64]
"""Types that may be cast to :class:`pandas.Timedelta`."""

Schedule = _t.Union[_pd.DatetimeIndex, DatetimeIterable, TimedeltaTypes]
"""User schedule type."""
Span = _t.Union[int, _t.Literal["all"], TimedeltaTypes]
"""User span type. Used to determine limits from the timestamps given by a :attr:`Schedule`."""
Flex = _t.Union[bool, _t.Literal["auto"], str]
"""Flexibility frequency string for ``floor/ceil``. Pass ``False`` to disable.

Options `'auto'` (**default**) and ``True`` are equivalent. Available data limits ``(start, end)`` are rounded using
:meth:`Timestamp.floor <pandas.Timestamp.floor>` and :meth:`Timestamp.ceil <pandas.Timestamp.ceil>`, respectively. In
other words, the start of the range is always rounded down while the end is rounded up.

Auto flex:
    When using ``flex='auto'`` (**default**), if and how bounds are expanded is determined by the size of the range and
    by distance between the actual and desired limits.

    Use :attr:`settings.auto_flex <rics.ml.time_split.settings.auto_flex>` to modify auto-flex behaviour.

Manual flex:
    Pass an :ref:`offset alias <pandas:timeseries.offset_aliases>` specify how limits should be rounded. To specify by
    `how much` limits may be rounded, pass ``'<'`` follow by a valid :class:`pandas.Timedelta`-string.

    See :func:`~rics.ml.time_split.support.expand_limits` for usage examples.
"""


class DatetimeSplitBounds(_t.NamedTuple):
    """A 3-tuple which denotes two adjacent datetime ranges."""

    start: _pd.Timestamp
    """Left (inclusive) limit of the `data` range."""
    mid: _pd.Timestamp
    """Schedule timestamp.

    Right (exclusive) limit of the `data` range, left (inclusive) limit of the `future_data` range.
    """
    end: _pd.Timestamp
    """Right (exclusive) limit of the `future_data` range."""


DatetimeSplits = _t.List[DatetimeSplitBounds]
"""A list of bounds."""


class DatetimeSplitCounts(_t.NamedTuple):
    """Relative importance of `data` and `future_data`."""

    data: int
    future_data: int
