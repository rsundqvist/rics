from collections.abc import Iterable
from datetime import date, datetime
from typing import Unpack

from polars import DataFrame, Series

from rics.misc import tname

from ..._docstrings import docs
from ...types import DatetimeIndexSplitterKwargs
from .._log_progress import LogProgressArg
from ..split_data import DatetimeSplit, split_data


@docs
def split_polars(
    data: DataFrame,
    time_column: str,
    *,
    log_progress: LogProgressArg = False,
    **kwargs: Unpack[DatetimeIndexSplitterKwargs],
) -> Iterable[DatetimeSplit[DataFrame]]:
    """Split a polars frame.

    Args:
        data: A ``polars.DataFrame``.
        time_column: A column to split on.
        log_progress: {log_progress}
        **kwargs: {DatetimeIndexSplitterKwargs}

    {USER_GUIDE}

    Yields:
        Tuples ``(data, future_data, bounds)``.

    Raises:
        TypeError: If `time_column` does not denote a datetime index-like field.

    """
    indexer = _Indexer(time_column)

    yield from split_data(
        data,
        log_progress=log_progress,
        as_available=indexer.as_available,
        select=indexer.select,
        **kwargs,
    )


class _Indexer:
    def __init__(self, time_column: str) -> None:
        self.time_column = time_column

    def as_available(self, data: DataFrame) -> Series:
        time = self._get_time(data)

        if isinstance(time[0], date):
            return time

        msg = f"Elements of data[{self.time_column!r}] element are {tname(time[0])}, expected datetime-like."
        raise TypeError(msg)

    def _get_time(self, data: DataFrame) -> Series:
        return data[self.time_column]

    def select(self, data: DataFrame, left: datetime, right: datetime) -> DataFrame:
        """Select data based on the given bounds."""
        time = self._get_time(data)
        return data.filter(time.is_between(left, right, closed="left"))
