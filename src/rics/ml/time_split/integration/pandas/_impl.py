from collections.abc import Hashable, Iterable
from datetime import date, datetime
from typing import Generic, TypeVar, Unpack

from pandas import DataFrame, DatetimeIndex, Series, Timestamp

from rics.misc import tname

from ..._docstrings import docs
from ...types import DatetimeIndexSplitterKwargs
from .._log_progress import LogProgressArg
from ..split_data import DatetimeSplit, split_data

PandasT = TypeVar("PandasT", Series, DataFrame)
"""A splittable pandas type."""


@docs
def split_pandas(
    data: PandasT,
    time_column: Hashable = None,
    *,
    log_progress: LogProgressArg = False,
    **kwargs: Unpack[DatetimeIndexSplitterKwargs],
) -> Iterable[DatetimeSplit[PandasT]]:
    """Split a pandas type.

    This function splits indexed data (i.e. ``Series`` and ``DataFrame``, not the index itself. Use
    :func:`time_split.split <rics.ml.time_split.split>` for pandas ``Index`` types, setting ``available=data.index``.

    Args:
        data: A pandas data container type to split; either ``Series`` or a ``DataFrame``.
        time_column: A column in `data` to split on. Use ``data`.index`` if ``None``.
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


class _Indexer(Generic[PandasT]):
    def __init__(self, time_column: Hashable | None) -> None:
        self.time_column = time_column

    def as_available(self, data: PandasT) -> Series | DatetimeIndex:
        time = self._get_time(data)

        first = time.iloc[0] if hasattr(time, "iloc") else time[0]
        if isinstance(first, date):
            return time

        type_str = "data.index" if self.time_column is None else f"data[{self.time_column!r}]"
        msg = f"Elements of {type_str} element are {tname(first)}, expected datetime-like."
        raise TypeError(msg)

    def _get_time(self, data: DataFrame) -> Series:
        return data.index if self.time_column is None else data[self.time_column]

    def select(self, data: PandasT, left: datetime, right: datetime) -> PandasT:
        """Select data based on the given bounds."""
        time = self._get_time(data)
        if isinstance(time, Series):
            return data[time.between(left, right, inclusive="left")]
        else:
            # Index slicing is a lot faster than boolean masks (empirically, seems to be a factor ~10).
            return data[left : right - Timestamp.resolution]  # type: ignore[misc]
