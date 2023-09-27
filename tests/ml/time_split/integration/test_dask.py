import pytest

from rics.ml.time_split import plot, split

dask_datasets = pytest.importorskip("dask.datasets", reason="support is undocumented")


def test_dask():
    available = dask_datasets.timeseries(end="2000-04", freq="5s").index
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
