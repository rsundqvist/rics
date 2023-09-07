from typing import Literal, NamedTuple, Optional, Protocol, Tuple, runtime_checkable

from pandas import DatetimeIndex, Timedelta, Timestamp, isna

from ..types import DatetimeIterable, DatetimeTypes, Flex

LimitsTuple = Tuple[Timestamp, Timestamp]


@runtime_checkable
class MinMaxDate(Protocol):
    """A type that has min/max functions returning a datetime-like scalar."""

    def min(self) -> DatetimeTypes:  # noqa: A003
        """Compute minimum datetime."""

    def max(self) -> DatetimeTypes:  # noqa: A003
        """Compute maximum datetime."""


class AvailableMetadata(NamedTuple):
    """Output of :func:`process_available`."""

    available_as_index: Optional[DatetimeIndex]
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
    if isinstance(available, MinMaxDate):
        # Avoids conversion, which may be expensive (or impossible on the current machine),
        # and leverages additional non-Pandas types that do vectorized min/max.
        limits = _compute_data_limits(available)
        available_retval = None
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

    expanded_limits = _expand_limits(flex, limits)
    return AvailableMetadata(available_retval, limits=limits, expanded_limits=expanded_limits)


def _compute_data_limits(available: MinMaxDate) -> LimitsTuple:
    min_dt, max_dt = available.min(), available.max()

    if (
        # Compatibility with Dask. One at a time is slower, but seems to use less memory.
        (hasattr(min_dt, "compute") and callable(min_dt.compute))
        and (hasattr(max_dt, "compute") and callable(max_dt.compute))
    ):
        min_dt = min_dt.compute()
        max_dt = max_dt.compute()

    return min_dt, max_dt


def _expand_limits(flex: Flex, limits: LimitsTuple) -> LimitsTuple:
    if flex is False:
        return limits

    if flex is True or flex == "auto":
        return _expand_limits(_auto_flex(limits), limits)

    if isinstance(flex, tuple):
        lo, hi = flex
    else:
        lo, hi = flex, flex

    return limits[0].floor(lo), limits[1].ceil(hi)


def _auto_flex(limits: LimitsTuple) -> Literal[False, "D"]:
    diff = limits[1] - limits[0]

    if diff >= Timedelta(days=2):
        return "D"

    return False
