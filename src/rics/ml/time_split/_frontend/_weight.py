from typing import Literal

from pandas import DatetimeIndex, Timedelta

from .._support import handle_dask
from ..types import DatetimeIterable, DatetimeSplitCounts, DatetimeSplits


def fold_weight(
    splits: DatetimeSplits,
    *,
    unit: str | Literal["rows", "hours", "days"] = "hours",
    available: DatetimeIterable | None = None,
) -> list[DatetimeSplitCounts]:
    """Compute fold weights.

    Args:
        splits: List of :attr:`~rics.ml.time_split.types.DatetimeSplitBounds`.
        unit: Time unit of the returned count, or `'rows'` (requires `available` data).
        available: Available data. Required when ``unit='rows'``.

    Returns:
        A list of tuples ``[(n_data_units, n_future_data_units), ...]``.

    Raises:
        ValueError: if ``unit='rows'`` and ``available=None``.

    """
    if unit == "rows":
        if available is None:
            raise ValueError(f"Must provide available data when {unit=}.")
        return _from_data(available, splits)
    else:
        return _from_unit(unit, splits)


def _from_unit(unit: str, splits: DatetimeSplits) -> list[DatetimeSplitCounts]:
    resolution = Timedelta(1, unit=unit)
    return [
        DatetimeSplitCounts(
            round((fold.mid - fold.start) / resolution),
            round((fold.end - fold.mid) / resolution),
        )
        for fold in splits
    ]


def _from_data(available: DatetimeIterable, splits: DatetimeSplits) -> list[DatetimeSplitCounts]:
    if hasattr(available, "to_series"):
        time = available.to_series()  # Works for Dask and Pandas.
    elif hasattr(available, "between"):
        time = available  # This is what we want. Dask index has this attribute, but calling it fails.
    else:
        time = DatetimeIndex(available).to_series()  # Coerce everything else.

    retval = []
    for fold in splits:
        data = time.between(fold.start, fold.mid, inclusive="left").sum()
        future_data = time.between(fold.mid, fold.end, inclusive="left").sum()

        data = handle_dask(data)
        future_data = handle_dask(future_data)

        retval.append(DatetimeSplitCounts(data, future_data=future_data))

    return retval
