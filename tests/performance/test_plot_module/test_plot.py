import contextlib
import json
import shutil
from functools import cache
from pathlib import Path
from typing import Any, cast

import pytest
from matplotlib import pyplot as plt

from rics.performance import plot_run
from rics.performance.plot_types import Kind
from rics.performance.types import ResultsDict

pytestmark = [
    pytest.mark.filterwarnings("ignore:.*points cannot be placed:UserWarning"),
    pytest.mark.filterwarnings("ignore:Results may be unreliable:UserWarning"),
    # pytest.mark.parametrize("kind", get_args(Kind)),  # For some reason, 'swarm' is very slow.
    pytest.mark.parametrize("kind", ["bar", "violin"]),
]

OUT_ROOT = Path(__file__).parent / "test-output/plots"
with contextlib.suppress(FileNotFoundError):
    shutil.rmtree(OUT_ROOT)


def run(kind: Kind, **kwargs: Any) -> None:
    run_results = get_run_results()
    if kind == "box":
        # seaborn==0.13.2 / matplotlib==3.10.0
        with pytest.warns(PendingDeprecationWarning, match="vert: bool will be deprecated"):
            facet_grid = plot_run(run_results, kind=kind, **kwargs)
    else:
        facet_grid = plot_run(run_results, kind=kind, **kwargs)

    plt.close(facet_grid.fig)


def test_default(kind: Kind) -> None:
    run(kind)


@pytest.mark.parametrize("estimator", ["min", "mean", "max"])
def test_estimator(kind: Kind, estimator: str) -> None:
    run(kind, estimator=estimator)


_GRID_RESULTS: ResultsDict = {
    "baseline": {("s100", 10): [1.0, 1.1], ("s100", 100): [1.2, 1.3], ("s1000", 10): [2.0, 2.1]},
    "optimized": {("s100", 10): [0.5, 0.6], ("s100", 100): [0.6, 0.7], ("s1000", 10): [0.7, 0.8]},
}
_GRID_NAMES = ["source", "rows"]


@pytest.mark.parametrize(
    "x, hue",
    [
        ("rows", "candidate"),  # named dim on x, candidate as hue
        ("candidate", "rows"),  # named dim as hue
        ("data", None),  # default hue (candidate)
        (None, "rows"),  # x auto-resolved
        (None, None),  # full default
    ],
)
def test_x_hue_from_named_dims(kind: Kind, x: str | None, hue: str | None) -> None:
    facet_grid = plot_run(_GRID_RESULTS, kind=kind, x=x, hue=hue, names=_GRID_NAMES, col="source")
    plt.close(facet_grid.fig)


def test_bad_x_raises(kind: Kind) -> None:
    with pytest.raises(ValueError, match="Bad x='nope'"):
        plot_run(_GRID_RESULTS, kind=kind, x="nope", names=_GRID_NAMES)


def test_relative_to(kind: Kind) -> None:
    facet_grid = plot_run(_GRID_RESULTS, kind=kind, relative_to="baseline", names=_GRID_NAMES, col="source", x="rows")
    # Speedup mode: the y-axis is the dimensionless 'speedup'.
    assert facet_grid.axes.flat[0].get_ylabel() == "speedup"
    # A reference line is drawn at 1.0 on every facet.
    for ax in facet_grid.axes.flat:
        ys = {tuple(line.get_ydata()) for line in ax.get_lines()}
        assert (1.0, 1.0) in ys
    plt.close(facet_grid.fig)


def test_relative_to_horizontal(kind: Kind) -> None:
    facet_grid = plot_run(_GRID_RESULTS, kind=kind, relative_to="baseline", names=_GRID_NAMES, horizontal=True)
    assert facet_grid.axes.flat[0].get_xlabel() == "speedup"
    plt.close(facet_grid.fig)


def test_relative_to_rejects_unit(kind: Kind) -> None:
    with pytest.raises(ValueError, match="dimensionless"):
        plot_run(_GRID_RESULTS, kind=kind, relative_to="baseline", unit="ms")


@cache
def get_run_results() -> ResultsDict:
    with Path(__file__).parent.joinpath("run-results.json").open("r") as f:
        results = json.load(f)
    return cast(ResultsDict, results)
