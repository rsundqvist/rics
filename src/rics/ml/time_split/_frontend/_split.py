from typing import Optional

from .._backend import DatetimeIndexSplitter
from .._docstrings import docs
from ..types import DatetimeIterable, DatetimeSplits, Flex, Schedule, Span


@docs
def split(
    schedule: Schedule,
    *,
    before: Span = "7d",
    after: Span = 1,
    n_splits: Optional[int] = None,
    available: DatetimeIterable = None,
    flex: Flex = "auto",
) -> DatetimeSplits:
    """Create time-based cross-validation splits.

    Args:
        schedule: {schedule}
        before: {before}
        after: {after}
        n_splits: {n_splits}
        available: {available} Passing a tuple ``(min, max)`` is enough.
        flex: {flex}

    {USER_GUIDE}

    Returns:
        A list of tuples ``[(start, mid, end), ...]``.
    """
    return DatetimeIndexSplitter(
        schedule,
        before=before,
        after=after,
        n_splits=n_splits,
        flex=flex,
    ).get_splits(available)
