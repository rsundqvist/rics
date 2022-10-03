"""Utility functions for :mod:`pandas`."""

from typing import Iterable, NamedTuple as _NamedTuple, Optional, Sequence, Tuple, Union

import pandas as pd

from rics.utility.misc import tname as _tname

_Schedule = Union[pd.DatetimeIndex, pd.Timedelta, Sequence, str]
_Span = Union[str, pd.Timedelta]


class TFold(_NamedTuple):
    """Named tuple type yielded by :meth:`tfold`."""

    time: pd.Timestamp
    """The scheduled time. Determined by the `schedule`-argument."""
    data: pd.DataFrame
    """Data before the scheduled `time`. Determined by the `before`-argument."""
    future_data: pd.DataFrame
    """("Future") data, after the scheduled `time`. Determined by the `after`-argument."""

    def __str__(self) -> str:
        data = self.data
        future_data = self.future_data
        return f"{_tname(self)}('{self.time}': {data.shape=}, {future_data.shape=})"


def tfold(
    df: pd.DataFrame,
    schedule: _Schedule = "1d",
    before: _Span = "5d",
    after: _Span = None,
    time_column: Optional[str] = "time",
) -> Iterable[TFold]:
    """Create temporal k-folds from a heterogeneous ``DataFrame``. Folds are closed on the right side.

    This method may be used to create temporal folds from heterogeneous/unaggregated data, typically used for training
    models (e.g. on raw transaction data). If your data is a well-formed time series, use the `TimeSeriesSplit`_ class
    from scikit-learn instead.

    Args:
        df: A pandas ``DataFrame``.
        schedule: Timestamps which denote the end dates of the folds (e.g. training dates). If a ``Timedelta`` or
            ``str``, create schedule from the start of ``df[time_column]``. Alternatively, you may pass a cron
            expression (requires ``croniter``).
        before: The period before the scheduled datetime to include for each iteration.
        after: The period after the scheduled datetime to include for each iteration. Set to ``None`` to dynamically
            adjust such that the after-period lasts until the next scheduled datetime.
        time_column: Column in `df` to base the folds on. Use index if ``None``.

    Yields:
        Tuples ``TFold(time, data, future_data)``.

    Examples:
        Iterating over folds.

        >>> df = pd.DataFrame({'time': pd.date_range('2022', '2022-1-15', freq='7h')})
        >>> for fold in tfold(df, schedule='68h', after='1d'): print(fold)
        TFold('2022-01-06 16:00:00': data.shape=(17, 1), future_data.shape=(3, 1))
        TFold('2022-01-09 12:00:00': data.shape=(18, 1), future_data.shape=(3, 1))
        TFold('2022-01-12 08:00:00': data.shape=(17, 1), future_data.shape=(4, 1))

        The ``TFold`` class is a named tuple, so it can be unpacked.

        >>> for t, d, fd in tfold(df, schedule='68h', after='1d'):
        ...     print(f"{t}: {len(d)=}, {len(fd)=}")
        2022-01-06 16:00:00: len(d)=17, len(fd)=3
        2022-01-09 12:00:00: len(d)=18, len(fd)=3
        2022-01-12 08:00:00: len(d)=17, len(fd)=4

    See Also:
        The :meth:`plot_tfold` method, which may be used to visualize temporal folds.

    .. _TimeSeriesSplit: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html
    """
    cuts, time = _parse_args(df, schedule, time_column, before, after)

    for start, mid, stop in cuts:
        yield TFold(
            time=mid,
            data=df[time.between(start, mid, inclusive="left")],
            future_data=df[time.between(mid, stop, inclusive="left")],
        )


def plot_tfold(
    df: pd.DataFrame,
    schedule: _Schedule = "1d",
    before: _Span = "5d",
    after: _Span = None,
    time_column: Optional[str] = "time",
) -> None:  # pragma: no cover
    """Plot the periods that would be returned by :meth:`tfold` if invoked with the same parameters.

    Args:
        df: A pandas ``DataFrame``.
        schedule: Timestamps which denote the end dates of the folds (e.g. training dates). If a ``Timedelta`` or
            ``str``, create schedule from the start of ``df[time_column]``. Alternatively, you may pass a cron
            expression (requires ``croniter``).
        before: The period before the scheduled datetime to include for each iteration.
        after: The period after the scheduled datetime to include for each iteration. Set to ``None`` to dynamically
            adjust such that the after-period lasts until the next scheduled datetime.
        time_column: Column in `df` to base the folds on. Use index if ``None``.

    Raises:
        ValueError: For empty ranges.

    Examples:
        Plotting cron folds. With ``after=None`` (the default), `Future data` expands until the next scheduled time.

        >>> from rics.utility import configure_stuff; configure_stuff()
        >>> df = pd.DataFrame({'time': pd.date_range('2022', '2022-2')})
        >>> plot_tfold(df, schedule='0 0 * * MON,FRI')

        .. image:: ../_images/folds.png

        The expression ``'0 0 * * MON,FRI'`` means `"every Monday and Frida at midnight"`.
    """
    import matplotlib.pyplot as plt
    from matplotlib.dates import AutoDateFormatter

    cuts = list(_parse_args(df, schedule, time_column, before, after)[0])

    if not cuts:
        raise ValueError("Cannot plot an empty range.")

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
        args.append(f"{time_column=}")
    ax.set_title(f"tfold({', '.join(args)})")
    ax.legend()
    fig.autofmt_xdate()


def _parse_args(
    df: pd.DataFrame, schedule: _Schedule, time_column: Optional[str], before: _Span, after: Optional[_Span]
) -> Tuple[Iterable[Tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp]], Union[pd.DatetimeIndex, pd.Series]]:
    time = df.index if time_column is None else df[time_column]
    cuts = _cuts(schedule, time, before, after)
    return cuts, time


def _handle_cron(expr: str, min_data: pd.Timestamp, max_dt: pd.Timestamp) -> pd.DatetimeIndex:
    try:
        from croniter import croniter_range

        return pd.DatetimeIndex(croniter_range(min_data, max_dt, expr))
    except ModuleNotFoundError as e:  # pragma: no cover
        raise ValueError(f"Install 'croniter' to parse cron expressions such such as '{expr}'.") from e


def _handle_schedule(
    schedule: _Schedule,
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
    schedule: _Schedule, time: Union[pd.DatetimeIndex, pd.Series], before: _Span, after: Optional[_Span]
) -> Iterable[Tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp]]:  # pragma: no cover
    min_dt, max_dt = time.agg(["min", "max"])
    parsed_schedule = _handle_schedule(schedule, min_dt, max_dt)

    for start, mid, stop in zip(
        parsed_schedule - pd.Timedelta(before),
        parsed_schedule,
        parsed_schedule[1:] if after is None else parsed_schedule + pd.Timedelta(after),
    ):
        if start < min_dt:
            continue
        if stop > max_dt:
            break

        yield start, mid, stop
