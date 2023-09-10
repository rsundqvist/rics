from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Tuple, Union

import pandas as pd
from pandas import Timestamp

from rics.misc import format_kwargs, tname

from .._backend import DatetimeIndexSplitter
from .._docstrings import docs
from ..settings import plot as settings
from ..types import DatetimeIterable, DatetimeSplits, Flex, Schedule, Span
from ._split import split
from ._weight import fold_weight

if TYPE_CHECKING:
    try:
        from matplotlib.pyplot import Axes
    except ModuleNotFoundError:
        Axes = Any


Rows = Literal["rows"]
COUNT_ROWS: Literal["rows"] = "rows"


@dataclass(frozen=True)
class _PlotData:
    splits: DatetimeSplits
    outer_range: Optional[Tuple[pd.Timestamp, pd.Timestamp]]
    available: Optional[DatetimeIterable]


@docs
def plot(
    schedule: Schedule,
    *,
    before: Span = "7d",
    after: Span = 1,
    n_splits: Optional[int] = None,
    available: DatetimeIterable = None,
    flex: Flex = "auto",
    # Split plot args
    bar_labels: Union[str, Rows, List[Tuple[str, str]], bool] = True,
    show_removed: bool = False,
    row_count_freq: str = None,
    ax: "Axes" = None,
) -> "Axes":
    """Visualize ranges in `splits`.

    Args:
        schedule: {schedule}
        before: {before}
        after: {after}
        n_splits: {n_splits}
        available: {available} If `bar_labels` is given but is not a ``list``,
            this data will be used to compute fold sizes.
        flex: {flex} Figures show the "real" (non-flex) outer data range.
        bar_labels: Labels to draw on the bars. If you pass a string, it will be interpreted as a time unit (see
            :ref:`pandas:timeseries.offset_aliases` for valid frequency strings). Bars will show the number of units
            contained. Pass `'rows'` to simply count the numbers of elements in `data` (if given). To write custom
            bar labels, pass a list ``[(data_label, future_data_label), ..]``, one tuple for each fold. This may be used
            to write metric values per data set after cross validation.
        show_removed: If ``True``, splits removed by `n_splits` are included in the figure.
        row_count_freq: A {OFFSET}. If given, show normalized row count per `row_count_freq` in the background.
        ax: Axis to use for plotting. If ``None``, create new axes.

    {USER_GUIDE}

    Returns:
        Matplitlib axes.

    Raises:
        ValueError: For invalid plot/split argument combinations.
    """
    import matplotlib.pyplot as plt
    from matplotlib.dates import AutoDateFormatter

    splitter = DatetimeIndexSplitter(
        schedule, before=before, after=after, n_splits=None if show_removed else n_splits, flex=flex
    )
    plot_data = _get_plot_data(available, splitter, skip_counts=isinstance(bar_labels, list) or not bar_labels)

    if bar_labels is True:
        bar_labels = settings.DEFAULT_TIME_UNIT if plot_data.available is None else COUNT_ROWS

    if ax is None:
        _, ax = plt.subplots(
            tight_layout=True,
            figsize=(plt.rcParams.get("figure.figsize")[0], 3 + len(plot_data.splits) * 0.5),
        )

    n_extra = len(plot_data.splits) - n_splits if n_splits else 0
    extra_args: Dict[str, Any]
    xtick: List[Timestamp] = []
    for i, (start, mid, stop) in enumerate(plot_data.splits, start=1):
        extra_args = {"alpha": 1} if i > n_extra else {"alpha": 0.35, "height": 0.6}
        ax.barh(i, mid - start, left=start, color="b", **extra_args)
        ax.barh(i, stop - mid, left=mid, color="r", **extra_args)

        xtick.append(mid)

    ax.containers[-2].set_label(settings.DATA_LABEL)
    ax.containers[-1].set_label(settings.FUTURE_DATA_LABEL)

    if bar_labels:
        _add_bar_labels(ax, plot_data, unit_or_labels=bar_labels)

    if plot_data.outer_range:
        left, right = plot_data.outer_range
        ax.axvline(left, color="k", ls="--", label="Outer range")
        ax.axvline(right, color="k", ls="--")
        xtick = [left, *xtick, right]

    ax.set_xticks(xtick)
    ax.xaxis.set_major_formatter(AutoDateFormatter(ax.xaxis.get_major_locator(), defaultfmt="%Y-%m-%d\n%A"))

    ax.set_ylabel("Fold")
    ax.yaxis.get_major_locator().set_params(integer=True)
    ticks = list(range(n_extra + 1, len(plot_data.splits) + 1))
    ax.yaxis.set_ticks(ticks, labels=[t - n_extra for t in ticks])

    split_kwargs = asdict(splitter)
    split_kwargs["n_splits"] = n_splits  # We may "incorrectly" set this to None to show excluded folds.
    ax.set_title(_make_title(available, split_kwargs))
    ax.legend(loc="lower right")

    if row_count_freq:
        if plot_data.available is None:
            raise ValueError(f"Cannot use {row_count_freq=} without available data.")

        time = plot_data.available if hasattr(plot_data.available, "floor") else pd.Series(plot_data.available).dt
        hourly = time.floor(row_count_freq).value_counts().sort_index()
        hourly *= max(ax.get_yticks()) / hourly.max()  # Normalize to folds
        print(hourly.max())
        ax.fill_between(hourly.index, hourly, alpha=0.2, color="grey")

    return ax


def _add_bar_labels(ax: "Axes", plot_data: _PlotData, *, unit_or_labels: Union[List[Tuple[str, str]], str]) -> None:
    if not (hasattr(ax, "bar_label") and callable(ax.bar_label)):
        raise TypeError(f"Given axes={ax!r} don't have a bar_label()-method.")

    if isinstance(unit_or_labels, list):
        labels = [e for t in unit_or_labels for e in t]
    else:
        labels = _make_count_labels(plot_data, unit_or_labels)

    for bar, label in zip(ax.containers, labels):
        ax.bar_label(bar, labels=[label], label_type="center")


def _make_count_labels(plot_data: _PlotData, unit_or_labels: str) -> List[str]:
    counts = fold_weight(plot_data.splits, unit=unit_or_labels, available=plot_data.available)

    suffix = settings.ROW_UNIT if unit_or_labels == COUNT_ROWS else unit_or_labels
    if len(suffix) > 1:
        suffix = " " + suffix

    def make_label(count: int) -> str:
        count_str = (
            f"{count:,}".replace(",", settings.THOUSANDS_SEPARATOR)
            if count >= settings.THOUSANDS_SEPARATOR_CUTOFF
            else str(count)
        )
        return count_str + suffix

    labels = []
    for data, future_data in counts:
        labels.append(make_label(data))
        labels.append(make_label(future_data))
    return labels


def _get_plot_data(
    available: Optional[DatetimeIterable], splitter: DatetimeIndexSplitter, skip_counts: bool
) -> _PlotData:
    if available is None:
        return _PlotData(
            splits=splitter.get_splits(),
            outer_range=None,
            available=None,
        )

    splits, ms = splitter.get_plot_data(available)
    return _PlotData(splits, ms.available_metadata.limits, available=None if skip_counts else available)


def _make_title(available: Any, split_kwargs: Dict[str, Any]) -> str:
    from inspect import signature

    default = {name: params.default for name, params in signature(split).parameters.items()}

    def should_print(key: str) -> bool:
        value = split_kwargs[key]
        default_value = default[key]
        try:
            return bool(value != default_value)
        except ValueError:
            return all(value != default_value)

    kwargs = {key: value for key, value in split_kwargs.items() if should_print(key)}
    formatted_args = ", ".join((tname(available), format_kwargs(kwargs)))
    return f"time_split.split({formatted_args})"
