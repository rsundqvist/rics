from typing import List, Tuple

import pandas as pd
import pytest
from matplotlib import pyplot as plt

from rics import configure_stuff
from rics.ml.time_split import plot, split

from .conftest import DATA_CASES, NO_DATA_CASES, NO_DATA_SCHEDULE, SPLIT_DATA

configure_stuff()


@pytest.mark.parametrize("kwargs, expected", *DATA_CASES)
def test_data(kwargs, expected):
    ax = plot(**kwargs, available=SPLIT_DATA)

    xtick_labels = [t.get_text() for t in ax.get_xticklabels()]

    # Outer bounds of SPLIT_DATA are added when data is given
    assert len(xtick_labels) == len(expected) + 2

    for i, (left, right) in enumerate(zip(xtick_labels[1:], expected)):
        # Only mid (index 1) is added
        assert left in right[1], i

    plt.close(ax.figure)


@pytest.mark.parametrize("after, expected", NO_DATA_CASES)
def test_no_data(after, expected):
    ax = plot(NO_DATA_SCHEDULE, after=after)

    xtick_labels = [t.get_text() for t in ax.get_xticklabels()]

    # No bounds when no available data is given
    assert len(xtick_labels) == len(expected)

    for i, (left, right) in enumerate(zip(xtick_labels, expected)):
        # Only mid (index 1) is added
        assert left in right[1], i

    plt.close(ax.figure)


@pytest.mark.parametrize("n_splits", [2, 4, 7])
def test_show_removed(n_splits):
    max_splits = len(split("3d", available=("2022", "2022-2")))
    assert n_splits <= max_splits, "bad test case"

    ax = plot("3d", available=("2022", "2022-2"), n_splits=n_splits, bar_labels=False, show_removed=True)
    xtick_labels = [t.get_text() for t in ax.get_yticklabels()]
    assert [str(n) for n in range(1, n_splits + 1)] == xtick_labels


@pytest.mark.parametrize("factory", [pd.Series, pd.Index, list])
def test_row_count_freq(factory, random_density_timestamps):
    available = factory(random_density_timestamps)
    plot("0 0 * * MON,FRI", available=available, row_count_freq="h")


@pytest.fixture(scope="module")
def random_density_timestamps() -> Tuple[pd.Timestamp, ...]:
    from numpy.random import choice, randint, seed

    seed(0)
    parts: List[pd.Timestamp] = []
    start = pd.Timestamp("1999-04-30")
    prev_size = 5000
    for _ in range(31 * 24):
        choices = pd.date_range(start, start + pd.Timedelta(hours=1), freq="5min", inclusive="left")
        size = prev_size + randint(-1000, 1000)
        if size < 500:
            size = 500 + randint(0, 500 - size)
        if size > 10_000:
            size = 10_000 + randint(0, size - 10_000)
        timestamps = choice(choices, size=size)
        parts.extend(timestamps)

        start = start + pd.Timedelta(hours=1)
        prev_size = size
    return tuple(parts)
