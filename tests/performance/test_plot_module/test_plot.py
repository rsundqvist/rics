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
    pytest.mark.filterwarnings("ignore:The test results may be unreliable:UserWarning"),
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


@cache
def get_run_results() -> ResultsDict:
    with Path(__file__).parent.joinpath("run-results.json").open("r") as f:
        results = json.load(f)
    return cast(ResultsDict, results)
