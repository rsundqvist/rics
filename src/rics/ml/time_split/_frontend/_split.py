from .._backend import DatetimeIndexSplitter
from .._docstrings import docs
from ..types import DatetimeIterable, DatetimeSplits, Flex, Schedule, Span


@docs
def split(
    schedule: Schedule,
    *,
    before: Span = "7d",
    after: Span = 1,
    step: int = 1,
    n_splits: int | None = None,
    available: DatetimeIterable | None = None,
    flex: Flex = "auto",
) -> DatetimeSplits:
    """Create time-based cross-validation splits.

    To visualize the folds, pass the same arguments to the :func:`.plot`-function.

    Args:
        schedule: {schedule}
        before: {before}
        after: {after}
        step: {step}
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
        step=step,
        n_splits=n_splits,
        flex=flex,
    ).get_splits(available)
