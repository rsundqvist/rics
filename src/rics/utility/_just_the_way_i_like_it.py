import logging
import warnings
from typing import Any, Union

import pandas as pd


def configure_stuff(
    level: Union[int, str] = logging.INFO, matplotlib_level: Union[int, str] = logging.WARNING, **kwargs: Any
) -> None:
    """Configure a bunch of stuff to match my personal preferences.

    Caveat Emptor: May do strange stuff 👻.

    Args:
        level: Root log level.
        matplotlib_level: Matplotlib log level.
        **kwargs: Keyword arguments for :meth:`rics.utility.logs.basic_config`.
    """
    from rics.utility.logs import basic_config

    pd.options.display.max_columns = 50
    pd.options.display.max_colwidth = 150
    pd.options.display.width = 0

    basic_config(level=level, matplotlib_level=matplotlib_level, **kwargs)

    try:
        from rics.utility.plotting import configure

        configure()
    except ModuleNotFoundError as e:
        warnings.warn(f"Plotting configuration not done: {e}")
