from typing import NamedTuple

from pandas import DatetimeIndex, Timestamp, isna

from .._support import handle_dask
from ..types import DatetimeIterable, Flex
from ._datetime_index_like import DatetimeIndexLike
from ._limits import LimitsTuple, expand_limits


class AvailableMetadata(NamedTuple):
    """Output of :func:`process_available`."""

    available_as_index: DatetimeIndexLike | None
    limits: LimitsTuple
    expanded_limits: LimitsTuple


def process_available(available: DatetimeIterable, *, flex: Flex) -> AvailableMetadata:
    """Process a user-given `available` argument.

    Args:
        available: Available data from user. May be ``None``
        flex: Flex-argument. Determines how much (if at all) to expand limits.

    Returns:
        A tuple ``(available, limits)``. Note that `available` will be ``None``, it has not been iterated over. This
        assures that iterables are not consumed unless needed.

    Raises:
        ValueError: For invalid `available` arguments.

    """
    if isinstance(available, DatetimeIndexLike):
        # Avoids conversion, which may be expensive (or impossible on the current machine),
        # and leverages additional non-Pandas types that do vectorized min/max.
        limits = _compute_data_limits(available)
        available_retval = available
    else:
        available_retval = DatetimeIndex(available)
        limits = _compute_data_limits(available_retval)

    min_dt, max_dt = limits
    if min_dt == max_dt or isna(min_dt) or isna(max_dt):
        raise ValueError("Not enough data in 'available'; at least two unique elements are required.")

    if not (isinstance(min_dt, Timestamp) and isinstance(max_dt, Timestamp)):
        # Enforce pandas types; we might have a numpy.datetime64
        # (croniter 1.4.1 + numpy 1.25.2): croniter cannot handle numpy.datetime64
        limits = Timestamp(min_dt), Timestamp(max_dt)

    expanded_limits = expand_limits(limits, flex=flex)
    return AvailableMetadata(available_retval, limits=limits, expanded_limits=expanded_limits)


def _compute_data_limits(available: DatetimeIndexLike) -> LimitsTuple:
    return handle_dask(available.min()), handle_dask(available.max())
