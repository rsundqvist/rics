r"""Integration with the Pandas library.

Examples:
    Splitting a ``pandas.Series`` with :func:`split_pandas`.

    >>> import pandas as pd
    >>> index = pd.date_range("2022", "2022-1-10", freq="h")
    >>> series = pd.Series(range(len(index)), index=index)
    >>> series.sample(3, random_state=1999)
    2022-01-04 00:00:00    72
    2022-01-03 21:00:00    69
    2022-01-04 14:00:00    86
    dtype: int64

    Series may only be split on the index. The `log_progress` keyword argument is optional.

    >>> for fold in split_pandas(
    ...     series, schedule="1d", log_progress="progress"
    ... ):  # doctest: +SKIP
    ...     print(
    ...         f"Summary of fold {tuple(map(pd.Timestamp.isoformat, fold.bounds))}:"
    ...         f"\n  {fold.data.mean()=}"
    ...         f"\n  {fold.future_data.mean()=}",
    ...     )
    INFO:progress:Begin fold 1/2: ('2022-01-01' <= [schedule: '2022-01-08' (Saturday)] < '2022-01-09').
    Summary of fold ('2022-01-01T00:00:00', '2022-01-08T00:00:00', '2022-01-09T00:00:00'):
      fold.data.mean()=83.5
      fold.future_data.mean()=179.5
    INFO:progress:Finished fold 1/2 [schedule: '2022-01-08' (Saturday)] after 1ms.  # doctest: +SKIP
    INFO:progress:Begin fold 2/2: ('2022-01-02' <= [schedule: '2022-01-09' (Sunday)] < '2022-01-10').
    Summary of fold ('2022-01-02T00:00:00', '2022-01-09T00:00:00', '2022-01-10T00:00:00'):
      fold.data.mean()=107.5
      fold.future_data.mean()=203.5
    INFO:progress:Finished fold 2/2 [schedule: '2022-01-09' (Sunday)] after 873μs.

    The ``split_pandas`` function returns :attr:`PandasDatetimeSplit`-tuples.


"""

from ._impl import PandasDatetimeSplit, PandasT, split_pandas

__all__ = [
    "PandasDatetimeSplit",
    "PandasT",
    "split_pandas",
]
