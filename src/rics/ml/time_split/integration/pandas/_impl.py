import sys
from dataclasses import dataclass
from typing import Generic, Hashable, Iterable, Literal, NamedTuple, Optional, Tuple, TypeVar, Union, get_args

import pandas as pd
from pandas import DataFrame, DatetimeIndex, Series, Timestamp

from rics.misc import tname

from ..._backend import DatetimeIndexSplitter
from ..._docstrings import docs
from ...types import DatetimeSplitBounds, Flex, Schedule, Span
from .._log_progress import LogProgressArg, handle_log_progress_arg

PandasT = TypeVar("PandasT", Series, DataFrame)
"""A splittable pandas type."""
Inclusive = Literal["left", "right", "neither"]

if sys.version_info < (3, 11):

    @dataclass(frozen=True)
    class PandasDatetimeSplit(Generic[PandasT]):
        """Time-based split of a pandas type."""

        data: PandasT
        """Data before ``bounds.mid``."""
        future_data: PandasT
        """Data after ``bounds.mid``."""
        bounds: DatetimeSplitBounds
        """The underlying bounds that produced this split."""

else:

    class PandasDatetimeSplit(NamedTuple, Generic[PandasT]):
        """Time-based split of a pandas type.

        .. warning::

           When running Python < 3.11, this is a ``@dataclass`` rather than a tuple.
        """

        data: PandasT
        """Data before ``bounds.mid``."""
        future_data: PandasT
        """Data after ``bounds.mid``."""
        bounds: DatetimeSplitBounds
        """The underlying bounds that produced this split."""


@docs
def split_pandas(
    data: PandasT,
    schedule: Schedule,
    *,
    before: Span = "7d",
    after: Span = 1,
    n_splits: Optional[int] = None,
    flex: Flex = "auto",
    time_column: Hashable = None,
    inclusive: Inclusive = "left",
    log_progress: LogProgressArg = False,
) -> Iterable[PandasDatetimeSplit[PandasT]]:
    """Split a pandas type.

    This function splits indexed data (i.e. ``Series`` and ``DataFrame``, not the index itself. Use
    :func:`time_split.split <rics.ml.time_split.split>` for pandas ``Index`` types, setting ``available=data.index``.

    Args:
        data: A pandas data container type to split.
        schedule: {schedule}
        before: {before}
        after: {after}
        n_splits: {n_splits}
        flex: {flex}
        time_column: A column in `data` to split on. Use index if ``None``.
        inclusive: Which side to make the splits inclusive on.
        log_progress: {log_progress}

    {USER_GUIDE}

    Yields:
        Tuples ``(data, future_data, bounds)``.

    Raises:
        TypeError: If the chosen split attribute is not a timestamp.
        ValueError: For disallowed `inclusive` values.
    """
    time = _verify_time_type(data, time_column)

    splits = DatetimeIndexSplitter(schedule, before, after=after, n_splits=n_splits, flex=flex).get_splits(time)
    tracked_splits = handle_log_progress_arg(log_progress, splits=splits)

    indexer = _Indexer(data, time=time, inclusive=inclusive)

    for bounds in splits if tracked_splits is None else tracked_splits:
        data, future_data = indexer(bounds)
        yield PandasDatetimeSplit(data, future_data=future_data, bounds=bounds)


@dataclass(frozen=True, eq=False, repr=False)
class _Indexer(Generic[PandasT]):
    data: PandasT
    time: Union[Series, DatetimeIndex]
    inclusive: Inclusive

    def __post_init__(self) -> None:
        inclusive = self.inclusive

        if inclusive in get_args(Inclusive):
            return

        if inclusive == "both":
            raise ValueError(f"Argument {inclusive=} is disabled, since this could cause make the folds overlap.")
        else:
            raise ValueError(f"Unknown argument {inclusive=}. Permitted options are {get_args(Inclusive)}.")

    def __call__(self, bounds: DatetimeSplitBounds) -> Tuple[PandasT, PandasT]:
        """Select data based on the given bounds."""
        start, mid, end = bounds
        data, time, inclusive = self.data, self.time, self.inclusive
        if isinstance(time, Series):
            return (
                data[time.between(start, mid, inclusive=inclusive)],
                data[time.between(mid, end, inclusive=inclusive)],
            )

        # Index slicing is a lot faster than boolean masks (empirically, seems to be a factor ~10).
        r = Timestamp.resolution
        if inclusive == "left":
            return data[start : mid - r], data[mid : end - r]
        if inclusive == "right":
            return data[start + r : mid], data[mid + r : end]

        return data[start + r : mid - r], data[mid + r : end - r]


def _verify_time_type(data: PandasT, time_column: Optional[Hashable]) -> Union[pd.DatetimeIndex, pd.Series]:
    first = data.index[0] if time_column is None else data[time_column].iloc[0]

    if isinstance(first, Timestamp):
        return data.index if time_column is None else data[time_column]

    type_str = "data.index" if time_column is None else f"data[{time_column!r}]"
    raise TypeError(f"Elements of {type_str} element are {tname(first)}, expected Timestamp.")
