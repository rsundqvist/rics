import contextlib
import json
import shutil
from functools import cache
from pathlib import Path
from typing import Any, cast, get_args

import pytest
from matplotlib import pyplot as plt

from rics.performance.types import ResultsDict

with pytest.warns(UserWarning, match="The rics.performance.plot API is experimental."):
    from rics.performance.plot import plot
    from rics.performance.plot.types import Kind

pytestmark = [
    pytest.mark.filterwarnings("ignore:.*points cannot be placed:UserWarning"),
    pytest.mark.filterwarnings("ignore:The test results may be unreliable:UserWarning"),
    pytest.mark.parametrize("kind", get_args(Kind)),
]

OUT_ROOT = Path(__file__).parent / "test-output/plots"
with contextlib.suppress(FileNotFoundError):
    shutil.rmtree(OUT_ROOT)


def run(kind: Kind, **kwargs: Any) -> None:
    root = OUT_ROOT.joinpath(*kwargs) if kwargs else OUT_ROOT.joinpath("default")
    name = "-".join([kind, *kwargs.values()]) + ".jpg"
    path = root / name
    assert not path.exists()

    results = run_results()
    if kind == "box":
        # seaborn==0.13.2 / matplotlib==3.10.0
        with pytest.warns(PendingDeprecationWarning, match="vert: bool will be deprecated"):
            facet_grid = plot(results, kind=kind, path=path, **kwargs)
    else:
        facet_grid = plot(results, kind=kind, path=path, **kwargs)

    plt.close(facet_grid.fig)


def test_default(kind: Kind) -> None:
    run(kind)


@pytest.mark.parametrize("estimator", ["min", "mean", "max"])
def test_estimator(kind: Kind, estimator: str) -> None:
    run(kind, estimator=estimator)


@cache
def run_results() -> ResultsDict:
    with Path(__file__).parent.joinpath("run-results.json").open("r") as f:
        results = json.load(f)
    return cast(ResultsDict, results)
