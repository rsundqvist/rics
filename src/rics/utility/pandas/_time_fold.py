import itertools
from typing import Iterable, Literal, NamedTuple, Optional, Sequence, Tuple, Union

import pandas as pd

from rics.utility.misc import tname

Schedule = Union[pd.DatetimeIndex, pd.Timedelta, Sequence, str]
Span = Union[int, str, Literal["all"], pd.Timedelta]


class TimeFold(NamedTuple):
    """Create temporal k-folds from a ``DataFrame`` for cross-validation.

    Use :meth:`TimeFold.iter` to create folds. Folds are closed on the right side (inclusive left).

    Examples:
        Iterating over folds using ``TimeFold.iter``.

        >>> df = pd.DataFrame({'time': pd.date_range('2022', '2022-1-15', freq='7h')})
        >>> for fold in TimeFold.iter(df, schedule='68h', after='1d'): print(fold)
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

        >>> for fold in TimeFold.iter(df, schedule='68h', before='all'): print(fold)
        TimeFold('2022-01-01 00:00:00': data.shape=(0, 1), future_data.shape=(10, 1))
        TimeFold('2022-01-03 20:00:00': data.shape=(10, 1), future_data.shape=(10, 1))
        TimeFold('2022-01-06 16:00:00': data.shape=(20, 1), future_data.shape=(10, 1))
        TimeFold('2022-01-09 12:00:00': data.shape=(30, 1), future_data.shape=(9, 1))

        Plotting folds using ``TimeFold.plot``.

        >>> from rics.utility import configure_stuff; configure_stuff()
        >>> df = pd.DataFrame({'time': pd.date_range('2022', '2022-2')})
        >>> TimeFold.plot(df, schedule='0 0 * * MON,FRI')

        .. image:: ../_images/folds.png

        The expression ``'0 0 * * MON,FRI'`` means `"every Monday and Friday at midnight"`.

        With ``after=1`` (the default), our `Future data` expands until the next scheduled time. This may be interpreted
        as `"taking a step forward"` in the schdule. Using integer `before` arguments works analogously, in the
        opposite direction.

    Notes:
       This method may be used to create temporal folds from heterogeneous/unaggregated data, typically used for
       training models (e.g. on raw transaction data). If your data is a well-formed time series, consider using the
       `TimeSeriesSplit`_ class from scikit-learn instead.

    .. _TimeSeriesSplit: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html
    """

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

        The ranges surrounding the scheduled datetimes may be dynamically chosen by setting `before` and/or `after` to:

            * ``'all'``: Include all data before/after the scheduled time, or
            * An ``int > 0``: Include all data `N` schedule periods before/after the current schedule datetime.
            * Any other values are passed as-is to the :class:`pandas.Timedelta` class.

        Args:
            df: A pandas ``DataFrame``.
            schedule: Timestamps which denote the end dates of the folds (e.g. training dates). If a ``Timedelta`` or
                ``str``, create schedule from the start of ``df[time_column]``. Alternatively, you may pass a cron
                expression (requires ``croniter``).
            before: The period before the scheduled datetime to include for each iteration.
            after: The period after the scheduled datetime to include for each iteration.
            time_column: Column in `df` to base the folds on. Use index if ``None``.

        Yields:
            Tuples ``TimeFold(time, data, future_data)``.

        See Also:
            The :meth:`plot` method, which may be used to visualize temporal folds.
        """
        cuts, time = _parse_args(df, schedule, time_column, before, after)

        for start, mid, stop in cuts:
            yield TimeFold(
                time=mid,
                data=df[time.between(start, mid, inclusive="left")],
                future_data=df[time.between(mid, stop, inclusive="left")],
            )

    @classmethod
    def plot(
        cls,
        df: pd.DataFrame,
        schedule: Schedule = "1d",
        before: Span = "5d",
        after: Span = 1,
        time_column: Optional[str] = "time",
    ) -> None:
        """Plot the intervals that would be returned by :meth:`iter` if invoked with the same parameters.

        The ranges surrounding the scheduled datetimes may be dynamically chosen by setting `before` and/or `after` to:

            * ``'all'``: Include all data before/after the scheduled time, or
            * An ``int > 0``: Include all data `N` schedule periods before/after the current schedule datetime.
            * Any other values are passed as-is to the :class:`pandas.Timedelta` class.

        Args:
            df: A pandas ``DataFrame``.
            schedule: Timestamps which denote the end dates of the folds (e.g. training dates). If a ``Timedelta`` or
                ``str``, create schedule from the start of ``df[time_column]``. Alternatively, you may pass a cron
                expression (requires ``croniter``).
            before: The period before the scheduled datetime to include for each iteration.
            after: The period after the scheduled datetime to include for each iteration.
            time_column: Column in `df` to base the folds on. Use index if ``None``.

        Raises:
            ValueError: For empty ranges.
        """
        import matplotlib.pyplot as plt
        from matplotlib.dates import AutoDateFormatter

        cuts = list(_parse_args(df, schedule, time_column, before, after)[0])

        if not cuts:
            raise ValueError("Cannot plot an empty range.")  # pragma: no cover

        fig, ax = plt.subplots(tight_layout=True)
        xticks = [cuts[0][0]]
        for i, (start, mid, stop) in enumerate(cuts):
            ax.barh(i, mid - start, left=start, color="b", label="Data" if i == 0 else None)
            ax.barh(i, stop - mid, left=mid, color="r", label="Future data" if i == 0 else None)
            xticks.append(mid)

        xticks.append(cuts[-1][-1])
        ax.xaxis.set_ticks(xticks)
        ax.set_yticks(range(len(cuts)))
        ax.xaxis.set_major_formatter(AutoDateFormatter(ax.xaxis.get_major_locator()))
        ax.set_ylabel("Fold")
        ax.set_xlabel("Time")
        args = [
            "df",
            f"{schedule=}" if isinstance(schedule, (str, pd.Timedelta)) else "[schedule..]",
            f"{before=}",
            f"{after=}",
        ]
        if time_column != "time":
            args.append(f"{time_column=}")  # pragma: no cover
        ax.set_title(f"TimeFold.iter({', '.join(args)})")
        ax.legend()
        fig.autofmt_xdate()

    def __str__(self) -> str:
        data = self.data
        future_data = self.future_data
        return f"{tname(self)}('{self.time}': {data.shape=}, {future_data.shape=})"


def _parse_args(
    df: pd.DataFrame, schedule: Schedule, time_column: Optional[str], before: Span, after: Optional[Span]
) -> Tuple[Iterable[Tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp]], Union[pd.DatetimeIndex, pd.Series]]:
    time = df.index if time_column is None else df[time_column]
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
) -> pd.DatetimeIndex:  # pragma: no cover
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
    schedule: Schedule, time: Union[pd.DatetimeIndex, pd.Series], before: Span, after: Span
) -> Iterable[Tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp]]:  # pragma: no cover
    min_dt, max_dt = time.agg(["min", "max"])
    parsed_schedule = _handle_schedule(schedule, min_dt, max_dt)

    if before == "all":
        before_iter = itertools.cycle([min_dt])
    elif isinstance(before, int):
        before_iter = parsed_schedule
        parsed_schedule = _handle_span(parsed_schedule, before, before=False)
    else:
        before_iter = _handle_span(parsed_schedule, before, before=True)

    for start, mid, stop in zip(
        before_iter,
        parsed_schedule,
        itertools.cycle([max_dt]) if after == "all" else _handle_span(parsed_schedule, after, before=False),
    ):
        if start < min_dt:
            continue
        if stop > max_dt:
            break
        if start > mid or mid > stop:
            continue

        yield start, mid, stop


def _handle_span(schedule: pd.DatetimeIndex, span: Span, before: bool) -> pd.DatetimeIndex:
    if isinstance(span, int):
        if span < 0:
            raise ValueError("Period offset cannot be negative.")  # pragma: no cover
        assert not before, "This isn't supposed to happen."  # noqa: S101

        return schedule[span:]
    else:
        offset = pd.Timedelta(span)
        if before:
            return schedule - offset
        else:
            return schedule + offset
