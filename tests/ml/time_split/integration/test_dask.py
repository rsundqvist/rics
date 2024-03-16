import pytest
from dask.datasets import timeseries
from rics.ml.time_split import plot, split
from rics.ml.time_split._backend._available import process_available

pytestmark = pytest.mark.filterwarnings(
    "ignore:The current Dask DataFrame implementation is deprecated.:DeprecationWarning"
)


@pytest.mark.parametrize("kind", ["index", "series"])
def test_dask(kind):
    df = timeseries(end="2000-04", freq="17 min", partition_freq="7d", dtypes={"x": int})
    if kind == "index":
        available = df.index
    else:
        df["time-column"] = df.index
        available = df["time-column"]
    kwargs = dict(schedule="7d", before="all", after="30 days", available=available)

    unlimited_splits = split(**kwargs)
    assert len(unlimited_splits) == 9
    assert unlimited_splits[-1].end.isoformat() == "2000-04-01T00:00:00"

    ax = plot(**kwargs, n_splits=5, show_removed=True, row_count_bin="1d")
    xtick_labels = [t.get_text() for t in ax.get_xticklabels()]
    assert len(xtick_labels) == len(unlimited_splits) + 2
    assert f"dask.dataframe.{kind.capitalize()}" in ax.get_title()

    for i, (left, right) in enumerate(zip(xtick_labels[1:], unlimited_splits)):
        # Only mid (index 1) is added
        assert left in str(right[1]), i

    splits = split(**kwargs, n_splits=5)
    assert len(splits) == 5
    assert splits[-1].end.isoformat() == "2000-04-01T00:00:00"
    assert splits[0] == unlimited_splits[-5]


def test_index_is_preserved():
    available = timeseries(freq="10 min").index

    actual = process_available(available, flex=False).available_as_index
    assert id(available) == id(actual)


def test_series_is_preserved():
    from dask.dataframe import Series  # type: ignore[attr-defined]

    available = timeseries(freq="10 min").index

    actual = process_available(available, flex=False).available_as_index
    assert isinstance(actual, Series)
