import logging
import warnings
from typing import Any, Union

from .logs import basic_config


def configure_stuff(
    level: Union[int, str] = logging.INFO,
    rics_level: Union[int, str] = logging.INFO,
    id_translation_level: Union[int, str] = logging.INFO,
    matplotlib_level: Union[int, str] = logging.WARNING,
    **kwargs: Any,
) -> None:
    """Configure a bunch of stuff to match my personal preferences. May do strange stuff 👻.

    .. warning::

       This function can and will change without warning, and will not be documented in the changelog. Don't use for
       anything important.

    Args:
        level: Log level for the root logger. Default is ``logging.INFO``.
        rics_level: Log level for the :mod:`rics` package. Default is ``logging.INFO``.
        id_translation_level: Log level for the :mod:`id_translation` package. Default is ``logging.INFO``.
        matplotlib_level: Log level for the :mod:`matplotlib` package. Default is ``logging.WARNING``.
        **kwargs: Keyword arguments for :py:func:`logging.basicConfig`.
    """
    basic_config(
        level=level,
        rics_level=rics_level,
        id_translation_level=id_translation_level,
        matplotlib_level=matplotlib_level,
        **kwargs,
    )

    _configure_pandas()

    try:
        from .plotting import configure

        configure()
    except ModuleNotFoundError as e:
        warnings.warn(f"Plotting configuration not done: {e}")


def _configure_pandas() -> None:
    try:
        import pandas as pd
    except ModuleNotFoundError as e:
        warnings.warn(f"Pandas configuration not done: {e}")
        return

        pd.options.display.max_columns = 50
        pd.options.display.max_colwidth = 150
        pd.options.display.max_rows = 250
        pd.options.display.width = 0
        pd.options.display.float_format = "{:.6g}".format

        pd.options.mode.chained_assignment = "raise"

    try:
        pd.plotting.register_matplotlib_converters()
    except ImportError:
        pass  # Likely a non-interactive environment
