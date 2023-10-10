from dask.datasets import timeseries

from rics.ml.time_split import plot, split
from rics.ml.time_split._backend._available import process_available


def test_dask():
    available = timeseries(end="2000-04", freq="5s").index
    kwargs = dict(schedule="7d", before="all", after="30 days", available=available)

    unlimited_splits = split(**kwargs)
    assert len(unlimited_splits) == 8

    ax = plot(**kwargs, n_splits=5, show_removed=True)
    xtick_labels = [t.get_text() for t in ax.get_xticklabels()]
    assert len(xtick_labels) == len(unlimited_splits) + 2

    for i, (left, right) in enumerate(zip(xtick_labels[1:], unlimited_splits)):
        # Only mid (index 1) is added
        assert left in str(right[1]), i

    assert len(split(**kwargs, n_splits=5)) == 5


def test_index_is_preserved():
    available = timeseries(freq="10 min").index

    actual = process_available(available, flex=False).available_as_index
    assert id(available) == id(actual)


def test_series_is_preserved():
    from dask.dataframe import Series  # type: ignore[attr-defined]

    available = timeseries(freq="10 min").index

    actual = process_available(available, flex=False).available_as_index
    assert isinstance(actual, Series)
