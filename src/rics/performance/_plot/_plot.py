import logging
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Literal

import pandas as pd

from rics.performance.plot_types import Kind, Unit
from rics.performance.types import ResultsDict

from ._params import CatplotParams
from ._postprocessors import make_postprocessors

if TYPE_CHECKING:
    import seaborn


def plot_run(
    run_results: ResultsDict | pd.DataFrame,
    *,
    x: Literal["candidate", "data"] | None = None,
    horizontal: bool = False,
    unit: Unit | None = None,
    kind: Kind = "bar",
    names: Iterable[str] = (),
    **kwargs: Any,
) -> "seaborn.FacetGrid":
    """Create a :func:`seaborn.catplot` from run results.

    .. figure:: /_images/perf_plot_facets.png

       Comparison of best-per-group selection functions (from the
       :ref:`examples </documentation/examples/notebooks/performance/best-by-group/Best-by-Group.ipynb>`
       page).

    The `names` argument:
        Names may be passed in combination with ``row`` and/or ``col`` arguments to add facets to the
        :func:`seaborn.catplot`. If given, the keys in the test data must be of type ``tuple`` with the same length as
        `names`. For example, if your test data looks like this:

        .. code-block::

           test_data = {
               ("+", 2,  5): +(2**5),
               ("+", 9,  5): +(9**5),
               ("+", 10, 5): +(10**5),
               ("-", 10, 3): -(10**3),
               ("-", 5,  3): -(5**3),
           }

        you may pass

        .. code-block::

           plot_run(
               run_results = ...,
               names=["sign", "base", "exponent"],
               col="sign",
               row="exponent",
           )

        to plot each sign/exponent in a separate facet, comparing only the exponents in the subplots.

    Args:
        run_results: Output of :meth:`.MultiCaseTimer.run`.
        x: X-axis quantity; ``candidate'`` or ``'data'``. The other will be used as the hue.
        horizontal: If ``True``, plot timings on the X-axis instead. The `x` becomes the new Y-axis quantity.
        unit: Y-axis time :attr:`~rics.performance.plot_types.Unit`.
        kind: The :attr:`~rics.performance.plot_types.Kind` of plot to draw.
        names: Test data level names.
        **kwargs: Keyword arguments for :func:`seaborn.catplot`.

    Returns:
        A :class:`seaborn.FacetGrid`.

    Raises:
        ModuleNotFoundError: If Seaborn isn't installed.
        TypeError: For unknown `unit` arguments.
    """
    params = CatplotParams.make(run_results, x=x, horizontal=horizontal, unit=unit, kind=kind, names=names, **kwargs)
    return plot_params(params)


def plot_params(params: CatplotParams) -> "seaborn.axisgrid.FacetGrid":
    """Create a :func:`seaborn.catplot` from :class:`CatplotParams`."""
    from seaborn import catplot

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

    return facet_grid
