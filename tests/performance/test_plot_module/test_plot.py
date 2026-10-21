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


def test_relative_to_excludes_baseline(kind: Kind) -> None:
    # The baseline is the reference line; it must not appear as a (flat 1.0) bar/hue.
    facet_grid = plot_run(_GRID_RESULTS, kind=kind, relative_to="baseline", names=_GRID_NAMES, hue="candidate")
    legend_texts = {t.get_text() for t in facet_grid.legend.texts} if facet_grid.legend else set()
    assert "baseline" not in legend_texts
    assert "optimized" in legend_texts
    plt.close(facet_grid.fig)


def test_relative_to_horizontal(kind: Kind) -> None:
    facet_grid = plot_run(_GRID_RESULTS, kind=kind, relative_to="baseline", names=_GRID_NAMES, horizontal=True)
    assert facet_grid.axes.flat[0].get_xlabel() == "speedup"
    plt.close(facet_grid.fig)


def test_relative_to_rejects_unit(kind: Kind) -> None:
    with pytest.raises(ValueError, match="dimensionless"):
        plot_run(_GRID_RESULTS, kind=kind, relative_to="baseline", unit="ms")


@pytest.mark.parametrize("horizontal", [False, True])
def test_log_scale_on_time_axis(kind: Kind, horizontal: bool) -> None:
    run_results: ResultsDict = {"slow": {"data": [1.0, 1.1]}, "fast": {"data": [0.001, 0.0011]}}
    facet_grid = plot_run(run_results, kind=kind, horizontal=horizontal)
    ax = facet_grid.axes.flat[0]
    assert (ax.get_xscale(), ax.get_yscale()) == (("log", "linear") if horizontal else ("linear", "log"))
    plt.close(facet_grid.fig)


def test_formatted_labels_keep_data_order(kind: Kind) -> None:
    run_results: ResultsDict = {"f": {("a", base): [1.0] for base in (2, 9, 10)}}
    facet_grid = plot_run(run_results, kind=kind, x="data", names=["source", "base"], col="source")
    ticks = [t.get_text() for t in facet_grid.axes.flat[0].get_xticklabels()]
    assert ticks == ["base = 2", "base = 9", "base = 10"]
    plt.close(facet_grid.fig)


@pytest.mark.parametrize(
    "labels",
    [[(10,), (100,)], [(10, "rows"), (100, "rows")], [(1, "a", 2.5), (2, "b", 3.5)]],
    ids=["1-tuple", "2-tuple", "3-tuple"],
)
@pytest.mark.parametrize("where", ["x", "hue", "horizontal"])
def test_tuple_labels_without_names(kind: Kind, labels: list[tuple[Any, ...]], where: str) -> None:
    run_results: ResultsDict = {"f": {label: [1.0] for label in labels}, "g": {label: [2.0] for label in labels}}
    kwargs = {"hue": "data"} if where == "hue" else {"x": "data", "horizontal": where == "horizontal"}
    facet_grid = plot_run(run_results, kind=kind, **kwargs)

    ax = facet_grid.axes.flat[0]
    if where == "hue":
        texts = [t.get_text() for t in facet_grid.legend.texts]
    else:
        texts = [t.get_text() for t in (ax.get_yticklabels() if where == "horizontal" else ax.get_xticklabels())]
    plt.close(facet_grid.fig)

    assert texts == [str(label) for label in labels]


@pytest.mark.parametrize("where", ["x", "hue"])
def test_tuple_labels_without_names_and_user_order(kind: Kind, where: str) -> None:
    labels = [(10, "r"), (100, "s")]

    def draw(keys: list[Any]) -> tuple[list[str], int]:
        run_results: ResultsDict = {"f": {k: [1.0] for k in keys}, "g": {k: [2.0] for k in keys}}
        order = keys[::-1]  # Reversed, so the user's order must be the one applied.
        kwargs: dict[str, Any] = (
            {"hue": "data", "hue_order": order} if where == "hue" else {"x": "data", "order": order}
        )
        facet_grid = plot_run(run_results, kind=kind, **kwargs)
        ax = facet_grid.axes.flat[0]
        texts = [t.get_text() for t in (facet_grid.legend.texts if where == "hue" else ax.get_xticklabels())]
        artists = len(ax.patches) + len(ax.collections)
        plt.close(facet_grid.fig)
        return texts, artists

    assert draw(labels) == draw([str(label) for label in labels])


@cache
def get_run_results() -> ResultsDict:
    with Path(__file__).parent.joinpath("run-results.json").open("r") as f:
        results = json.load(f)
    return cast(ResultsDict, results)
