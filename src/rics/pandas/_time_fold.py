import itertools
import logging
import os
from datetime import timedelta
from typing import TYPE_CHECKING, Any, Iterable, List, Literal, NamedTuple, Optional, Sequence, Tuple, Union

import pandas as pd
from numpy import ndarray

from ..logs import disable_temporarily
from ..misc import tname

if TYPE_CHECKING or os.environ.get("SPHINX_BUILD"):
    from matplotlib.pyplot import Figure

Schedule = Union[pd.DatetimeIndex, pd.Timedelta, timedelta, Sequence, str]
Span = Union[int, str, Literal["all"], pd.Timedelta, timedelta]

LOGGER = logging.getLogger(__package__).getChild("TimeFold")


class DatetimeSplitter:
    """See :meth:`TimeFold.make_sklearn_splitter`."""

    def __init__(
        self,
        schedule: Schedule,
        before: Span,
        after: Span,
        time_column: Optional[str],
    ) -> None:
        self._schedule = schedule
        self._before = before
        self._after = after
        self._column = time_column

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
        self, X: pd.DataFrame = None, y: Union[pd.DataFrame, pd.Series] = None, groups: Any = None
    ) -> Iterable[Tuple[List[int], List[int]]]:
        """Generate indices to split data into training and test set.

        Args:
            X: Training data (features). Must be a ``Pandas`` type.
            y: Target variable. Must be a ``Pandas`` type.
            groups: Always ignored, exists for compatibility.

        Yields:
            The training/test set indices for that split.

        Raises:
            ValueError: If both `X` and `y` are ``None``.
        """
        cuts, time = (None, None) if X is None else self._parse_args(X, "X")
        if y is None:
            pass  # pragma: no cover
        else:
            cuts, time = self._parse_args(y, "y", expected_time=time)

        if cuts is None:
            raise ValueError("At least one of (X, y) must be given.")  # pragma: no cover

        for start, mid, stop in cuts:
            train, test = time.between(start, mid, inclusive="left"), time.between(mid, stop, inclusive="left")
            yield list(time.index[train]), list(time.index[test])

    def _parse_args(
        self,
        data: Union[pd.DataFrame, pd.Series],
        name: str,
        expected_time: pd.Series = None,
    ) -> Tuple[Iterable[Tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp]], pd.Series]:
        if self._column and isinstance(data, pd.Series):
            raise TypeError(f"Cannot process Series-type '{name}'-argument unless time_column=None.")

        cuts, time = _parse_args(data, self._schedule, time_column=self._column, before=self._before, after=self._after)
        if expected_time is not None:
            try:
                pd.testing.assert_series_equal(expected_time, time)
            except AssertionError as e:  # pragma: no cover
                raise ValueError("Indices of X and y must be equal. See trace for details.") from e
        else:
            pass  # pragma: no cover

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
       * - String ``'all```
         - Include all data before/after the scheduled time.
       * - ``int > 0``
         - Include all data within `N` schedule periods from the scheduled time.
       * - Anything else
         - Passed as-is to the :class:`pandas.Timedelta` class. Must be positive.

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
        >>> df = pd.DataFrame({'time': pd.date_range('2022', '2022-1-21')})
        >>> TimeFold.plot(df, schedule='0 0 * * MON,FRI')

        .. image:: ../_images/folds.png

        The expression ``'0 0 * * MON,FRI'`` means `"every Monday and Friday at midnight"`.

        With ``after=1`` (the default), our `Future data` expands until the next scheduled time. This may be interpreted
        as `"taking a step forward"` in the schedule. Using integer `before` arguments works analogously, in the
        opposite direction. Vertical lines indicate outer limits of `df`.

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
    ) -> Iterable["TimeFold"]:
        """Create temporal k-folds from a heterogeneous ``DataFrame``.

        Args:
            df: A pandas ``DataFrame``.
            schedule: Timestamps which denote the anchor dates of the folds (e.g. training dates). If a ``Timedelta`` or
                ``str``, create schedule from the start of ``df[time_column]``. Alternatively, you may pass a cron
                expression (requires ``croniter``).
            before: The period before the scheduled time to include. See :ref:`ba-args`
            after: The period after the scheduled time to include. See :ref:`ba-args`
            time_column: Column to base the folds on. Use index if ``None``.

        Yields:
            Tuples ``TimeFold(time, data, future_data)``.

        See Also:
            The :meth:`TimeFold.plot` method, which may be used to visualize temporal folds.
        """
        cuts, time = _parse_args(df, schedule, time_column, before, after)

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
    ) -> DatetimeSplitter:
        """Create a scikit-learn compatible splitter.

        Args:
            schedule: Timestamps which denote the anchor dates of the folds (e.g. training dates). If a ``Timedelta`` or
                ``str``, create schedule from the start of ``df[time_column]``. Alternatively, you may pass a cron
                expression (requires ``croniter``).
            before: The period before the scheduled time to include. See :ref:`ba-args`
            after: The period after the scheduled time to include. See :ref:`ba-args`
            time_column: Column to base the folds on. Use index if ``None``. If given, the returned splitter will not
                be able to handle y-arguments.

        Returns:
            A sklearn-compatible splitter backed by :meth:`TimeFold.iter`.

        See Also:
            The :meth:`TimeFold.plot` method, which may be used to visualize temporal folds.
        """
        return DatetimeSplitter(schedule, before=before, after=after, time_column=time_column)

    @classmethod
    def plot(
        cls,
        df: pd.DataFrame,
        schedule: Schedule = "1d",
        before: Span = "5d",
        after: Span = 1,
        time_column: Optional[str] = "time",
        **kwargs: Any,
    ) -> "Figure":
        """Plot the intervals that would be returned by :meth:`TimeFold.iter` if invoked with the same parameters.

        Args:
            df: A pandas ``DataFrame``.
            schedule: Timestamps which denote the anchor dates of the folds (e.g. training dates). If a ``Timedelta`` or
                ``str``, create schedule from the start of ``df[time_column]``. Alternatively, you may pass a cron
                expression (requires ``croniter``).
            before: The period before the scheduled time to include for each iteration. See :ref:`ba-args`
            after: The period after the scheduled time to include for each iteration. See :ref:`ba-args`
            time_column: Column to base the folds on. Use index if ``None``.
            **kwargs: Keyword arguments for :func:`matplotlib.pyplot.subplots`.

        Returns:
            A ``Figure``  object.

        Raises:
            ValueError: For empty ranges.
        """
        import matplotlib.pyplot as plt
        from matplotlib.dates import AutoDateFormatter

        cuts, time = _parse_args(df, schedule, time_column, before, after)
        cuts = list(cuts)

        if not cuts:
            raise ValueError("Cannot plot an empty range.")  # pragma: no cover

        fig, ax = plt.subplots(**{"tight_layout": True, **kwargs})

        if isinstance(ax, ndarray):
            ax = ax.flatten()[0]

        xticks = [cuts[0][0]]
        for i, (start, mid, stop) in enumerate(cuts):
            ax.barh(i, mid - start, left=start, color="b", label="Data" if i == 0 else None)
            ax.barh(i, stop - mid, left=mid, color="r", label="Future data" if i == 0 else None)
            xticks.append(mid)

        ax.axvline(time.min(), color="k", ls="--")
        ax.axvline(time.max(), color="k", ls="--")

        xticks.append(cuts[-1][-1])
        ax.xaxis.set_ticks(xticks)
        ax.set_yticks(range(len(cuts)))
        ax.xaxis.set_major_formatter(AutoDateFormatter(ax.xaxis.get_major_locator()))
        ax.set_ylabel("Fold")
        ax.set_xlabel("Time")
        args = [
            "df",
            _repr_schedule(schedule),
            f"{before=}",
            f"{after=}",
        ]
        if time_column != "time":
            args.append(f"{time_column=}")  # pragma: no cover
        ax.set_title(f"TimeFold.iter({', '.join(args)})")
        ax.legend(loc="upper left")
        fig.autofmt_xdate()

        return fig

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
) -> Tuple[Iterable[Tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp]], pd.Series]:
    time = pd.Series(
        pd.to_datetime(data.index if time_column is None else data[time_column], infer_datetime_format=True)
    )

    cuts = _cuts(schedule, time, before, after)
    return cuts, time


def _handle_cron(expr: str, min_data: pd.Timestamp, max_dt: pd.Timestamp) -> pd.DatetimeIndex:
    try:
        from croniter import croniter_range

        return pd.DatetimeIndex(croniter_range(min_data, max_dt, expr))
    except ModuleNotFoundError as e:
        raise ValueError(f"Install 'croniter' to parse cron expressions such such as '{expr}'.") from e


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
        raise ValueError("Schedule timestamps must be in sorted order.")  # pragma: no cover

    return schedule


def _cuts(
    schedule: Schedule, time: Union[pd.DatetimeIndex, pd.Series], before: Span, after: Span
) -> Iterable[Tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp]]:
    if LOGGER.isEnabledFor(logging.INFO):
        with disable_temporarily(LOGGER):
            num_folds = len(list(_cuts(schedule, time, before, after)))

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

        fold_idx += 1
        if LOGGER.isEnabledFor(logging.INFO):
            LOGGER.info(f"Yield fold {fold_idx}/{num_folds}: {pretty_fold}")

        yield start, mid, stop


def _handle_span(schedule: pd.DatetimeIndex, span: Span, before: bool) -> pd.DatetimeIndex:
    span_repr = f"offset {'before' if before else 'after'}={repr(span)}. Offsets must be non-negative."

    if isinstance(span, int):
        if span < 0:
            raise ValueError(f"Bad period {span_repr}")  # pragma: no cover
        assert not before, "This isn't supposed to happen."  # noqa: S101

        return schedule[span:]
    else:
        offset = pd.Timedelta(span)
        if offset < pd.Timedelta(0):
            raise ValueError(f"Bad timedelta {span_repr}")  # pragma: no cover

        if before:
            return schedule - offset
        else:
            return schedule + offset


def _repr_schedule(schedule: Schedule) -> str:
    return f"{schedule=}" if isinstance(schedule, (str, pd.Timedelta, timedelta)) else "schedule=[time..]"
