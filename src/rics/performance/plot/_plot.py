import logging
from pathlib import Path
from typing import Any, Literal

import pandas as pd
from seaborn import FacetGrid, catplot

from rics.performance.types import ResultsDict

from ._params import CatplotParams
from ._postprocessors import make_postprocessors
from .types import Unit


def plot(
    run_results: ResultsDict | pd.DataFrame,
    x: Literal["candidate", "data"] | None = None,
    *,
    unit: Unit | None = None,
    path: str | Path | None = None,
    **kwargs: Any,
) -> FacetGrid:
    params = CatplotParams.make(run_results, x=x, unit=unit, **kwargs)
    return plot_params(params, path=path)


def plot_params(
    params: CatplotParams,
    *,
    path: str | Path | None = None,
) -> FacetGrid:
    kwargs = params.to_kwargs()
    postprocessors = make_postprocessors(kwargs)
    facet_grid = catplot(**kwargs)

    logger = logging.getLogger(__package__).getChild("plot")
    if logger.isEnabledFor(logging.DEBUG):
        from rics.misc import get_public_module

        without_data = kwargs.copy()
        shape = without_data.pop("data").shape
        pretty_func = get_public_module(catplot) + "." + catplot.__qualname__
        logger.debug(
            f"Calling {pretty_func}(DataFrame[{' x '.join(map(str, shape))}], **kwargs) with:"
            f"\n - {params=}"
            f"\n - kwargs={without_data}"
            f"\n - {postprocessors=}",
            extra=without_data,
        )

    facet_grid.set_titles()

    for p in postprocessors:
        p(facet_grid)

    if path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        facet_grid.fig.savefig(path)

    return facet_grid
