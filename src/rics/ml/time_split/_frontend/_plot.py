from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Set, Tuple, Union

import pandas as pd
from pandas import Timestamp

from rics.misc import format_kwargs, get_public_module
from rics.performance import format_seconds

from .._backend import DatetimeIndexSplitter
from .._backend._datetime_index_like import DatetimeIndexLike
from .._backend._limits import LimitsTuple
from .._docstrings import docs
from ..settings import plot as settings
from ..types import DatetimeIterable, DatetimeSplitBounds, DatetimeSplits, Flex, Schedule, Span
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
class Available:
    """Metadata concerning the `available` data passed by the user."""

    index: DatetimeIndexLike
    true_limits: LimitsTuple
    expanded_limits: LimitsTuple


@dataclass(frozen=True)
class PlotData:
    """Data used for plotting."""

    splits: DatetimeSplits
    """All splits to plot."""
    removed: Set[DatetimeSplitBounds]
    """A subset of `splits` that should be plotted that would be filtered by user arguments."""
    row_counts: Optional[pd.Series] = None
    """Row counts for `available`. May be pre-computed by the user."""
    available: Optional[Available] = None


@docs
def plot(
    schedule: Schedule,
    *,
    before: Span = "7d",
    after: Span = 1,
    step: int = 1,
    n_splits: Optional[int] = None,
    available: DatetimeIterable = None,
    flex: Flex = "auto",
    # Split plot args
    bar_labels: Union[str, Rows, List[Tuple[str, str]], bool] = True,
    show_removed: bool = False,
    row_count_bin: Union[str, pd.Series] = None,
    ax: "Axes" = None,
) -> "Axes":
    """Fold visualization.

    This function plots the folds and in-fold splits that would be made by passing the same arguments to the
    :func:`.split`-function.

    Args:
        schedule: {schedule}
        before: {before}
        after: {after}
        step: {step}
        n_splits: {n_splits}
        available: {available} If `bar_labels` is given but is not a ``list``,
            this data will be used to compute fold sizes.
        flex: {flex}
        bar_labels: Labels to draw on the bars. If you pass a string, it will be interpreted as a time unit (see
            :ref:`pandas:timeseries.offset_aliases` for valid frequency strings). Bars will show the number of units
            contained. Pass `'rows'` to simply count the numbers of elements in `data` (if given). To write custom
            bar labels, pass a list ``[(data_label, future_data_label), ...]``, one tuple for each fold. This may be
            used to write metric values per data set after cross validation.
        show_removed: If ``True``, splits removed by `n_splits` or `step` are included in the figure.
        row_count_bin: A {OFFSET}. If given, show normalized row count per `row_count_bin` in the background. Pass
            ``pandas.Series`` to use pre-computed row counts.
        ax: Axis to use for plotting. If ``None``, create new axes.

    {USER_GUIDE}

    Returns:
        Matplitlib axes.

    Raises:
        ValueError: For invalid plot/split argument combinations.
    """
    import matplotlib.pyplot as plt

    splitter = DatetimeIndexSplitter(
        schedule,
        before=before,
        after=after,
        step=step,
        n_splits=n_splits,
        flex=flex,
    )
    plot_data = _get_plot_data(available, splitter, row_count_bin=row_count_bin, show_removed=show_removed)

    if bar_labels is True:
        bar_labels = settings.DEFAULT_TIME_UNIT if plot_data.available is None else COUNT_ROWS

    if ax is None:
        _, ax = plt.subplots(
            tight_layout=True,
            figsize=(plt.rcParams.get("figure.figsize")[0], 3 + len(plot_data.splits) * 0.5),
        )

    _plot_splits(ax, plot_data.splits, removed=plot_data.removed)

    if bar_labels:
        _add_bar_labels(ax, plot_data, unit_or_labels=bar_labels, label_type="center", font="monospace")

    # Set title
    split_kwargs = asdict(splitter)
    split_kwargs["n_splits"] = n_splits  # We may "incorrectly" set this to None to show excluded folds.
    ax.set_title(_make_title(available, split_kwargs))

    if plot_data.available is None:
        ax.legend(loc=("lower" if splitter.step > 0 else "upper") + " right")
        return ax

    _plot_limits(ax, plot_data.available.expanded_limits)

    if plot_data.row_counts is not None:
        assert isinstance(row_count_bin, (str, pd.Series))  # noqa: S101
        _plot_row_counts(ax, row_count_bin, plot_data.row_counts)

    ax.legend(loc=("lower" if splitter.step > 0 else "upper") + " right")

    return ax


def _plot_limits(ax: "Axes", limits: LimitsTuple) -> None:
    from matplotlib.dates import date2num

    left, right = limits
    ax.axvline(left, color="k", ls="--", label="Outer range")
    ax.axvline(right, color="k", ls="--")
    ax.set_xticks([date2num(left), *ax.get_xticks(), date2num(right)])


def _plot_splits(ax: "Axes", splits: DatetimeSplits, *, removed: Set[DatetimeSplitBounds]) -> None:
    from matplotlib.dates import AutoDateFormatter

    kwargs: Dict[str, Any]
    xtick: List[Timestamp] = []
    ytick: List[Optional[int]] = []
    for i, (start, mid, stop) in enumerate(splits, start=1):
        blue_label, red_label = None, None
        if (start, mid, stop) in removed:
            kwargs = settings.REMOVED_FOLD_STYLE
            ytick.append(None)
        else:
            kwargs = {"alpha": 1}
            fold_no = 1 + sum(1 for t in ytick if t is not None)
            ytick.append(fold_no)
            if fold_no == 1:
                blue_label, red_label = settings.DATA_LABEL, settings.FUTURE_DATA_LABEL

        ax.barh(i, mid - start, left=start, color="b", label=blue_label, **kwargs)
        ax.barh(i, stop - mid, left=mid, color="r", label=red_label, **kwargs)
        xtick.append(mid)

    ax.set_xticks(xtick)
    ax.xaxis.set_major_formatter(AutoDateFormatter(ax.xaxis.get_major_locator(), defaultfmt="%Y-%m-%d\n%A"))

    ax.set_ylabel("Fold")
    ax.yaxis.get_major_locator().set_params(integer=True)
    ax.yaxis.set_ticks(range(1, len(splits) + 1), labels=["" if t is None else t for t in ytick])


def _plot_row_counts(ax: "Axes", row_count_bin: Union[str, pd.Series], row_counts: pd.Series) -> None:
    if isinstance(row_count_bin, pd.Series):
        from numpy import diff, timedelta64

        row_counts = row_count_bin.sort_index()
        pretty = format_seconds(diff(row_counts.index).min() / timedelta64(1, "s"))
    else:
        row_counts = row_counts.sort_index()
        pretty = format_seconds(pd.Timedelta(row_count_bin).total_seconds())

    row_counts = row_counts * (max(ax.get_yticks()) / row_counts.max())  # Normalize to fold number yaxis
    ax.fill_between(row_counts.index, row_counts, alpha=0.2, color="grey", label=f"#rows [bin: {pretty}]")


def _add_bar_labels(
    ax: "Axes", plot_data: PlotData, *, unit_or_labels: Union[List[Tuple[str, str]], str], **kwargs: Any
) -> None:
    if not (hasattr(ax, "bar_label") and callable(ax.bar_label)):
        raise TypeError(f"Given axes={ax!r} don't have a bar_label()-method.")

    if isinstance(unit_or_labels, list):
        labels = [e for t in unit_or_labels for e in t]
    else:
        labels = _make_count_labels(
            plot_data.splits,
            available=None if plot_data.available is None else plot_data.available.index,
            unit=unit_or_labels,
        )

    for bar, label in zip(ax.containers, labels):
        ax.bar_label(bar, labels=[label], **kwargs)


def _make_count_labels(
    splits: DatetimeSplits, *, available: Optional[DatetimeIterable], unit: str = COUNT_ROWS
) -> List[str]:
    counts = fold_weight(splits, unit=unit, available=available)

    suffix = settings.ROW_UNIT if unit == COUNT_ROWS else unit
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
    available: Optional[DatetimeIterable],
    splitter: DatetimeIndexSplitter,
    *,
    row_count_bin: Union[pd.Series, str, None],
    show_removed: bool,
) -> PlotData:
    splits, ms = splitter.get_plot_data(available)
    available = ms.available_metadata.available_as_index

    if show_removed:
        kept_splits = set(splits)
        kwargs = asdict(splitter)  # Can't use dataclasses.replace: 3.10+ only
        kwargs["n_splits"] = None
        kwargs["step"] = 1
        splits = DatetimeIndexSplitter(**kwargs).get_plot_data(available)[0]
        if splitter.step < 0:
            splits.reverse()
        removed = set(splits) - set(kept_splits)
    else:
        removed = set()

    row_counts = _compute_row_counts(available, row_count_bin=row_count_bin)

    if available is None:
        return PlotData(splits, removed=removed)
    else:
        return PlotData(
            splits,
            removed=removed,
            row_counts=row_counts,
            available=Available(
                index=available,
                true_limits=ms.available_metadata.limits,
                expanded_limits=ms.available_metadata.expanded_limits,
            ),
        )


def _compute_row_counts(
    available: Optional[DatetimeIndexLike], *, row_count_bin: Union[pd.Series, str, None]
) -> Optional[pd.Series]:
    if row_count_bin is None:
        return None

    if isinstance(row_count_bin, pd.Series):
        return row_count_bin

    if available is None:
        raise ValueError(f"Cannot use {row_count_bin=} without available data.")

    index_like = available
    if hasattr(index_like, "dt"):
        # pandas series, dask datetime index
        index_like = index_like.dt
    elif not hasattr(index_like, "floor"):
        a_type = get_public_module(type(available), resolve_reexport=True, include_name=True)
        raise TypeError(f"type(available)={a_type} must have one of `floor` and `dt` to use {row_count_bin=}")

    row_counts = index_like.floor(row_count_bin).value_counts()
    if hasattr(row_counts, "compute") and callable(row_counts.compute):
        row_counts = row_counts.compute()
    return row_counts


def _make_title(available: Optional[Any], split_kwargs: Dict[str, Any]) -> str:
    from inspect import signature

    default = {name: params.default for name, params in signature(split).parameters.items()}

    def is_default(key: str) -> bool:
        try:
            return bool(split_kwargs[key] == default[key])
        except ValueError:
            return all(split_kwargs[key] == default[key])

    kwargs = {key: value for key, value in split_kwargs.items() if not is_default(key)}
    if available is None:
        formatted_available = ""
    else:
        pretty = get_public_module(type(available), resolve_reexport=True, include_name=True)
        formatted_available = f", available={pretty}"
    return f"time_split.split({format_kwargs(kwargs, max_value_length=40)}{formatted_available})"
