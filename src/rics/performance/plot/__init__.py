"""Plotting backend for the performance framework.

.. warning::

   This API is NOT stable.
"""

import warnings

from ._params import CatplotParams
from ._plot import plot, plot_params
from ._postprocessors import make_postprocessors

warnings.warn(message="The rics.performance.plot API is experimental.", stacklevel=2)

__all__ = ["CatplotParams", "plot", "plot_params", "make_postprocessors"]
