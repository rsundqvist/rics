r"""Integration with the Polars library.

Examples:
    Splitting a ``polars.DataFrame`` with :func:`split_polars`.

    >>> import polars as pl
    >>> from datetime import date
    >>> ts = pl.datetime_range(
    ...     date.fromisoformat("2022-01-01"),
    ...     date.fromisoformat("2022-01-10"),
    ...     interval="1h",
    ...     eager=True,
    ... )
    >>> df = pl.DataFrame({"timestamp": ts, "ints": range(len(ts))})
    >>> df.sample(5, seed=1999)
    shape: (5, 2)
    ┌─────────────────────┬──────┐
    │ timestamp           ┆ ints │
    │ ---                 ┆ ---  │
    │ datetime[μs]        ┆ i64  │
    ╞═════════════════════╪══════╡
    │ 2022-01-06 16:00:00 ┆ 136  │
    │ 2022-01-08 17:00:00 ┆ 185  │
    │ 2022-01-01 06:00:00 ┆ 6    │
    │ 2022-01-01 05:00:00 ┆ 5    │
    │ 2022-01-03 08:00:00 ┆ 56   │
    └─────────────────────┴──────┘

    To split the frame, pass it to ``split_polars`` along with the column to split on. The `schedule` keyword argument
    is required, but `log_progress` is not.

    >>> for fold in split_polars(
    ...     df, schedule="1d", log_progress="progress", time_column="timestamp"
    ... ):  # doctest: +SKIP
    ...     print(
    ...         f"Summary of fold {tuple(map(pd.Timestamp.isoformat, fold.bounds))}:"
    ...         f"\n  {fold.data['ints'].mean()=}"
    ...         f"\n  {fold.future_data['ints'].mean()=}",
    ...     )
    INFO:progress:Begin fold 1/2: '2022-01-01' <= [schedule: '2022-01-08' (Saturday)] < '2022-01-09'.
    Summary of fold ('2022-01-01T00:00:00', '2022-01-08T00:00:00', '2022-01-09T00:00:00'):
      fold.data['ints'].mean()=83.5
      fold.future_data['ints'].mean()=179.5
    INFO:progress:Finished fold 1/2: [schedule: '2022-01-08' (Saturday)] after 542μs.
    INFO:progress:Begin fold 2/2: '2022-01-02' <= [schedule: '2022-01-09' (Sunday)] < '2022-01-10'.
    Summary of fold ('2022-01-02T00:00:00', '2022-01-09T00:00:00', '2022-01-10T00:00:00'):
      fold.data['ints'].mean()=107.5
      fold.future_data['ints'].mean()=203.5
    INFO:progress:Finished fold 2/2: [schedule: '2022-01-09' (Sunday)] after 433μs.

"""

from ._impl import split_polars

__all__ = [
    "split_polars",
]
