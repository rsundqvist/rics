import itertools
import logging
import os
import warnings
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Iterable, List, Literal, NamedTuple, Optional, Sequence, Tuple, Union

import pandas as pd
from numpy import ndarray

from ..logs import disable_temporarily
from ..misc import tname

if TYPE_CHECKING or os.environ.get("SPHINX_BUILD"):
    from matplotlib.pyplot import Axes

Schedule = Union[pd.DatetimeIndex, pd.Timedelta, timedelta, Sequence, str]
Span = Union[int, str, Literal["all"], pd.Timedelta, timedelta]
SplittableTypes = Optional[Union[pd.DataFrame, pd.Series, Iterable[pd.Timestamp], Iterable[datetime], Iterable[str]]]

LOGGER = logging.getLogger(__package__).getChild("TimeFold")


# Would be nice to inherit a base splitter here, but these scikit-learn splitters aren't very typing-friendly..
class DatetimeSplitter:
    """See :meth:`TimeFold.make_sklearn_splitter`."""

    def __init__(
        self,
        schedule: Schedule,
        before: Span,
        after: Span,
        time_column: Optional[str],
        n_splits: int = None,
    ) -> None:
        self._schedule = schedule
        self._before = before
        self._after = after
        self._column = time_column
        self._n_splits = n_splits

    def __repr__(self) -> str:
        before = self._before
        after = self._after
        return f"TimeFold.make_sklearn_splitter({self._schedule}, {before=}, {after=})"

    def get_n_splits(self, X: pd.DataFrame = None, y: Union[pd.DataFrame, pd.Series] = None, groups: Any = None) -> int:
        """Returns the number of splitting iterations with the given arguments."""
        if X is None and y is None:
            raise ValueError("At least one of (X, y) must be given.")  # pragma: no cover

        data, name = (X, "X") if y is None else (y, "y")
        with disable_temporarily(LOGGER):
            return len(list(self._parse_args(data, name=name)[0]))

    def split(
        self,
        X: SplittableTypes = None,
        y: SplittableTypes = None,
        groups: Any = None,
    ) -> Iterable[Tuple[List[int], List[int]]]:
        """Generate indices to split data into training and test set.

        Args:
            X: Training data (features).
            y: Target variable.
            groups: Always ignored, exists for compatibility.

        Yields:
            The training/test set indices for that split.

        Raises:
            ValueError: If both `X` and `y` are ``None``.
        """
        cuts, time = (None, None) if X is None else self._parse_args(X, "X")
        if y is None:
            pass
        else:
            cuts, time = self._parse_args(y, "y", expected_time=time)

        if cuts is None:
            raise ValueError("At least one of (X, y) must be given.")

        for start, mid, stop in cuts:
            train, test = time.between(start, mid, inclusive="left"), time.between(mid, stop, inclusive="left")
            yield list(time.index[train]), list(time.index[test])

    def _parse_args(
        self,
        data: SplittableTypes,
        name: str,
        expected_time: pd.Series = None,
    ) -> Tuple[Iterable[Tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp]], pd.Series]:
        data = _parse_data_arg(data, time_column=self._column, name=name)

        cuts, time = _parse_args(
            data,
            self._schedule,
            time_column=self._column,
            before=self._before,
            after=self._after,
            n_splits=self._n_splits,
        )
        if expected_time is not None:
            try:
                pd.testing.assert_series_equal(expected_time, time)
            except AssertionError as e:
                raise ValueError("Indices of X and y must be equal. See trace for details.") from e
        else:
            pass

        return cuts, time


class TimeFold(NamedTuple):
    """Create temporal k-folds from a ``DataFrame`` for cross-validation.

    Folds are closed on the right side (inclusive left).

    Use :meth:`TimeFold.iter` to create folds, or :meth:`TimeFold.make_sklearn_splitter` to create a scikit-learn
    compatible splitter for cross validation.

    The ranges surrounding the :attr:`scheduled times <time>` are determined by the `before` and `after` arguments,
    interpreted as follows based on type:

    .. _ba-args:
    .. list-table:: Before/after argument options.
       :header-rows: 1

       * - Argument type
         - Interpretation
       * - String ``'all'``
         - Include all data before/after the scheduled time. Equivalent to ``max_train_size=None`` when using
           `TimeSeriesSplit`_.
       * - ``int > 0``
         - Include all data within `N` schedule periods from the scheduled time.
       * - Anything else
         - Passed as-is to the :class:`pandas.Timedelta` class. Must be positive. See
           :ref:`pandas:timeseries.offset_aliases` for valid frequency strings.

    Folds always lie fully within the available time span, but empty :attr:`data` or :attr:`future_data` frames are
    possible if the data is not continuous.

    Examples:
        Iterating over folds using ``TimeFold.iter``.

        >>> df = pd.DataFrame({'time': pd.date_range('2022', '2022-1-15', freq='7h')})
        >>> for fold in TimeFold.iter(df, schedule='68h', after='1d'):
        ...     print(fold)
        TimeFold('2022-01-06 16:00:00': data.shape=(17, 1), future_data.shape=(3, 1))
        TimeFold('2022-01-09 12:00:00': data.shape=(18, 1), future_data.shape=(3, 1))
        TimeFold('2022-01-12 08:00:00': data.shape=(17, 1), future_data.shape=(4, 1))

        The ``TimeFold`` class is a named tuple, so it can be unpacked.

        >>> for t, d, fd in TimeFold.iter(df, schedule='68h', after='1d'):
        ...     print(f"{t}: {len(d)=}, {len(fd)=}")
        2022-01-06 16:00:00: len(d)=17, len(fd)=3
        2022-01-09 12:00:00: len(d)=18, len(fd)=3
        2022-01-12 08:00:00: len(d)=17, len(fd)=4

        Including all data before the scheduled time.

        >>> for fold in TimeFold.iter(df, schedule='68h', before='all'):
        ...    print(fold)
        TimeFold('2022-01-03 20:00:00': data.shape=(10, 1), future_data.shape=(10, 1))
        TimeFold('2022-01-06 16:00:00': data.shape=(20, 1), future_data.shape=(10, 1))
        TimeFold('2022-01-09 12:00:00': data.shape=(30, 1), future_data.shape=(9, 1))

        Plotting folds using ``TimeFold.plot``.

        >>> from rics import configure_stuff; configure_stuff()
        >>> data = pd.date_range('2022', '2022-1-21', freq='38min')
        >>> TimeFold.plot(data, schedule='0 0 * * MON,FRI', before='all')

        .. image:: ../_images/folds.png

        The expression ``'0 0 * * MON,FRI'`` means `"every Monday and Friday at midnight"`. The numbers shown are the
        row counts for the fold.

        With ``after=1`` (the default), our `Future data` expands until the next scheduled time. This may be interpreted
        as `"taking a step forward"` in the schedule. Using integer `before` arguments works analogously, in the
        opposite direction. Vertical lines indicate outer limits of the data.

    Notes:
       This method may be used to create temporal folds from heterogeneous/unaggregated data, typically used for
       training models (e.g. on raw transaction data). If your data is a well-formed time series, consider using the
       `TimeSeriesSplit`_ class from scikit-learn instead.

    .. _TimeSeriesSplit: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html
    """  # noqa: E501

    time: pd.Timestamp
    """The scheduled time. Determined by the `schedule`-argument."""
    data: pd.DataFrame
    """Data before the scheduled `time`. Determined by the `before`-argument."""
    future_data: pd.DataFrame
    """("Future") data, after the scheduled `time`. Determined by the `after`-argument."""

    @classmethod
    def iter(  # noqa: A003
        cls,
        df: pd.DataFrame,
        schedule: Schedule = "1d",
        before: Span = "5d",
        after: Span = 1,
        time_column: Optional[str] = "time",
        n_splits: int = None,
    ) -> Iterable["TimeFold"]:
        """Create temporal k-folds from a heterogeneous ``DataFrame``.

        Args:
            df: A pandas ``DataFrame``.
            schedule: Timestamps which denote the anchor dates of the folds (e.g. training dates). If a ``Timedelta`` or
                ``str``, create schedule from the start of ``df[time_column]``. Alternatively, you may pass a cron
                expression (requires ``croniter``).
            before: The period before the scheduled time to include. See :ref:`ba-args`
            after: The period after the scheduled time to include. See :ref:`ba-args`
            n_splits: Maximum number of splits, preferring later folds. Has no effects if the actual number of splits
                given `df` is less than `n_splits`.
            time_column: Column to base the folds on if ``DataFrame``-type data is given, ignored otherwise. Pass
                ``None`` to use  ``DataFrame.index``.

        Yields:
            Tuples ``TimeFold(time, data, future_data)``.

        See Also:
            The :meth:`TimeFold.plot` method, which may be used to visualize temporal folds.
        """
        cuts, time = _parse_args(df, schedule, time_column, before, after, n_splits)

        for start, mid, stop in cuts:
            yield TimeFold(
                time=mid,
                data=df[time.between(start, mid, inclusive="left").values],
                future_data=df[time.between(mid, stop, inclusive="left").values],
            )

    @classmethod
    def make_sklearn_splitter(
        cls,
        schedule: Schedule = "1d",
        before: Span = "5d",
        after: Span = 1,
        time_column: str = None,
        n_splits: int = None,
    ) -> DatetimeSplitter:
        """Create a scikit-learn compatible splitter.

        Args:
            schedule: Timestamps which denote the anchor dates of the folds (e.g. training dates). If a ``Timedelta`` or
                ``str``, create schedule from the start of ``df[time_column]``. Alternatively, you may pass a cron
                expression (requires ``croniter``).
            before: The period before the scheduled time to include. See :ref:`ba-args`
            after: The period after the scheduled time to include. See :ref:`ba-args`
            time_column: Column to base the folds on if ``DataFrame``-type data is given, ignored otherwise. Pass
                ``None`` to use  ``DataFrame.index``.
            n_splits: Maximum number of splits, preferring later folds. Has no effects if the actual number of splits
                given `df` is less than `n_splits`.

        Returns:
            A sklearn-compatible splitter backed by :meth:`TimeFold.iter`.

        See Also:
            The :meth:`TimeFold.plot` method, which may be used to visualize temporal folds.
        """
        return DatetimeSplitter(schedule, before=before, after=after, time_column=time_column, n_splits=n_splits)

    @classmethod
    def plot(
        cls,
        data: SplittableTypes,
        schedule: Schedule = "1d",
        before: Span = "5d",
        after: Span = 1,
        time_column: Optional[str] = "time",
        n_splits: int = None,
        ax: "Axes" = None,
        show_counts: bool = None,
        **kwargs: Any,
    ) -> "Axes":
        """Plot the intervals that would be returned by :meth:`TimeFold.iter` if invoked with the same parameters.

        Args:
            data: Something to split.
            schedule: Timestamps which denote the anchor dates of the folds (e.g. training dates). If a ``Timedelta`` or
                ``str``, create schedule from the start of ``data[time_column]``. Alternatively, you may pass a cron
                expression (requires ``croniter``).
            before: The period before the scheduled time to include for each iteration. See :ref:`ba-args`
            after: The period after the scheduled time to include for each iteration. See :ref:`ba-args`
            time_column: Column to base the folds on if ``DataFrame``-type data is given, ignored otherwise. Pass
                ``None`` to use  ``DataFrame.index``.
            n_splits: Maximum number of splits, preferring later folds. Has no effects if the actual number of splits
                given `df` is less than `n_splits`.
            ax: Axis to use for plotting. Creates a new figure using :func:`matplotlib.pyplot.subplots` if ``None``.
            show_counts: If ``True``, data set sizes by calling :func:`matplotlib.pyplot.bar_label`. Set to
                ``None`` to choose automatically based on ``matplotlib``-version.
            **kwargs: Keyword arguments for :func:`matplotlib.pyplot.subplots`. Default arguments:
                ``{"tight_layout": True, "figsize": (<default-width>, 3 + 0.5 * num_folds)}``

        Returns:
            A ``Figure``  object.

        Raises:
            ValueError: For empty ranges.
        """
        import matplotlib.pyplot as plt
        from matplotlib.dates import AutoDateFormatter
        from matplotlib.pyplot import Axes

        args = [
            "data",
            _repr_schedule(schedule),
            f"{before=}",
            f"{after=}",
        ]
        if time_column != "time":
            args.append(f"{time_column=}")

        if time_column == "time" and not isinstance(data, pd.DataFrame):
            time_column = None  # Time is the default arg, but irrelevant for anything except DataFrame data

        if time_column is None:
            x_axis_label = (data.name or "time") if hasattr(data, "name") else "time"  # type:ignore[union-attr]
        else:
            x_axis_label = time_column

        data = _parse_data_arg(data, time_column=time_column)
        cuts, time = _parse_args(data, schedule, time_column, before, after, n_splits)
        with disable_temporarily(LOGGER):
            cuts = list(cuts)

        if not cuts:
            raise ValueError("Cannot plot an empty range.")  # pragma: no cover

        if ax is None:
            user_axis = False
            default_figure_kwargs = {
                "tight_layout": True,
                "figsize": (plt.rcParams.get("figure.figsize")[0], 3 + len(cuts) * 0.5),
            }
            _, ax = plt.subplots(**{**default_figure_kwargs, **kwargs})
            if isinstance(ax, ndarray):
                ax = ax.flatten()[0]
        else:
            user_axis = True
            if kwargs:  # pragma: no cover
                warnings.warn(
                    f"Keyword arguments {kwargs} for matplotlib.pyplot.subplots"
                    " are ignored since an explicit axis is given.",
                    stacklevel=2,
                )

        xticks = [cuts[0][0]]
        counts: List[str] = []
        for i, (start, mid, stop) in enumerate(cuts, start=1):
            ax.barh(i, mid - start, left=start, color="b", label="Data" if i == 1 else None)
            ax.barh(i, stop - mid, left=mid, color="r", label="Future data" if i == 1 else None)

            counts.append(time.between(start, mid, inclusive="left").sum())
            counts.append(time.between(mid, stop, inclusive="left").sum())

            xticks.append(mid)

        if hasattr(Axes, "bar_label") if show_counts is None else show_counts:
            for bar, count in zip(ax.containers, counts):
                ax.bar_label(bar, labels=[str(count)], label_type="center")

        ax.axvline(time.min(), color="k", ls="--", label="Outer range")
        ax.axvline(time.max(), color="k", ls="--")

        xticks.append(cuts[-1][-1])
        ax.xaxis.set_ticks(xticks)
        ax.xaxis.set_major_formatter(AutoDateFormatter(ax.xaxis.get_major_locator()))
        ax.set_ylabel("Fold")
        ax.set_xlabel(x_axis_label)
        ax.set_title(f"TimeFold.iter({', '.join(args)})")
        ax.legend(loc="lower right")

        if not user_axis:
            ax.figure.autofmt_xdate()

        return ax

    def __str__(self) -> str:
        data = self.data
        future_data = self.future_data
        return f"{tname(self)}('{self.time}': {data.shape=}, {future_data.shape=})"


def _parse_args(
    data: Union[pd.DataFrame, pd.Series],
    schedule: Schedule,
    time_column: Optional[str],
    before: Span,
    after: Optional[Span],
    n_splits: Optional[int],
) -> Tuple[Iterable[Tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp]], pd.Series]:
    time = pd.Series(pd.to_datetime(data.index if time_column is None else data[time_column]))

    cuts = _cuts(schedule, time, before, after, n_splits)
    return cuts, time


def _handle_cron(expr: str, min_data: pd.Timestamp, max_dt: pd.Timestamp) -> pd.DatetimeIndex:
    try:
        from croniter import croniter_range

        return pd.DatetimeIndex(croniter_range(min_data, max_dt, expr))
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(f"Install 'croniter' to parse cron expressions such such as '{expr}'.") from e


def _handle_schedule(
    schedule: Schedule,
    min_dt: pd.Timestamp,
    max_dt: pd.Timestamp,
) -> pd.DatetimeIndex:
    if isinstance(schedule, str):
        if " " in schedule or schedule[0] == "@":
            return _handle_cron(schedule, min_dt, max_dt)
        else:
            schedule = pd.Timedelta(schedule)

    if isinstance(schedule, pd.Timedelta):
        return pd.date_range(
            start=min_dt.ceil(schedule.resolution_string),
            end=max_dt.floor(schedule.resolution_string),
            freq=schedule,
        )

    if not isinstance(schedule, pd.DatetimeIndex):
        schedule = pd.DatetimeIndex(schedule)

    if any(schedule.sort_values() != schedule):
        raise ValueError("Schedule timestamps must be in sorted order.")

    return schedule


def _cuts(
    schedule: Schedule,
    time: Union[pd.DatetimeIndex, pd.Series],
    before: Span,
    after: Span,
    n_splits: Optional[int],
    allow_recurse: bool = True,
) -> Iterable[Tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp]]:
    if n_splits is not None and n_splits < 1:
        raise ValueError(f"Expected n_splits >= 1 but got {n_splits=}.")

    number_to_skip = 0
    if allow_recurse and (LOGGER.isEnabledFor(logging.INFO) or n_splits):
        with disable_temporarily(LOGGER):
            num_folds = len(list(_cuts(schedule, time, before, after, n_splits, allow_recurse=False)))

        if n_splits is not None:
            number_to_skip = num_folds - n_splits
            num_folds = min(n_splits, num_folds)

    min_dt, max_dt = time.min(), time.max()
    parsed_schedule = _handle_schedule(schedule, min_dt, max_dt)

    if before == "all":
        before_iter = itertools.cycle([min_dt])
    elif isinstance(before, int):
        before_iter = parsed_schedule
        parsed_schedule = _handle_span(parsed_schedule, before, before=False)
    else:
        before_iter = _handle_span(parsed_schedule, before, before=True)

    if LOGGER.isEnabledFor(logging.INFO):
        data_start = str(min_dt)
        data_end = str(max_dt)
        LOGGER.info(
            f"Create time folds using ({_repr_schedule(schedule)}, {before=}, {after=}) restricted to range ({data_start=}, {data_end=})."
        )

    fold_idx = 0
    num_valid_fold_skipped = 0

    for start, mid, stop in zip(
        before_iter,
        parsed_schedule,
        itertools.cycle([max_dt]) if after == "all" else _handle_span(parsed_schedule, after, before=False),
    ):
        if LOGGER.isEnabledFor(logging.INFO):
            pretty_fold = f"('{start}' <= [schedule: '{mid}'] < '{stop}')"

        if start < min_dt:
            if LOGGER.isEnabledFor(logging.DEBUG):
                LOGGER.debug(f"Skip fold {pretty_fold}: Begins before {data_start=}.")

            continue
        if stop > max_dt:
            if LOGGER.isEnabledFor(logging.DEBUG):
                LOGGER.debug(f"Skip fold {pretty_fold}: Ends after {data_end=}.")
            continue
        if start >= mid or mid >= stop:
            if LOGGER.isEnabledFor(logging.DEBUG):
                details = []
                if start >= mid:
                    details.append(f"fold_start >= [schedule: '{mid}']")
                if mid >= stop:
                    details.append(f"[schedule: '{mid}'] >= fold_stop")
                LOGGER.debug(f"Skip fold {pretty_fold} since {'and'.join(details)}.")
            continue

        if num_valid_fold_skipped < number_to_skip:
            if LOGGER.isEnabledFor(logging.DEBUG):
                LOGGER.debug(f"Skip fold {pretty_fold}: Rejected by {n_splits=}.")
            num_valid_fold_skipped += 1
            continue

        fold_idx += 1
        if LOGGER.isEnabledFor(logging.INFO):
            LOGGER.info(f"Yield fold {fold_idx}/{num_folds}: {pretty_fold}")

        yield start, mid, stop


def _handle_span(schedule: pd.DatetimeIndex, span: Span, before: bool) -> pd.DatetimeIndex:
    span_repr = f"offset {'before' if before else 'after'}={repr(span)}. Offsets must be non-negative."

    if isinstance(span, int):
        if span < 0:
            raise ValueError(f"Bad period {span_repr}")
        assert not before, "This isn't supposed to happen."  # noqa: S101

        return schedule[span:]
    else:
        offset = pd.Timedelta(span)
        if offset < pd.Timedelta(0):
            raise ValueError(f"Bad timedelta {span_repr}")

        if before:
            return schedule - offset
        else:
            return schedule + offset


def _repr_schedule(schedule: Schedule) -> str:
    return f"{schedule=}" if isinstance(schedule, (str, pd.Timedelta, timedelta)) else "schedule=[time..]"


def _parse_data_arg(
    data: SplittableTypes,
    time_column: Optional[str],
    name: str = "data",
) -> Union[pd.DataFrame, pd.Series]:
    if isinstance(data, pd.DataFrame):
        return data

    if time_column is not None:
        raise TypeError(f"Cannot process {type(data).__name__}-type '{name}'-argument unless time_column=None.")

    return data if isinstance(data, pd.Series) else pd.Series(index=pd.DatetimeIndex(data), dtype=int)
