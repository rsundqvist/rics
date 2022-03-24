import logging
from typing import Union


def configure_stuff(level: Union[int, str] = logging.INFO, matplotlib_level: Union[int, str] = logging.WARNING) -> None:
    """Configure a bunch of stuff to match my personal preferences.

    Caveat Emptor: May do strange stuff 👻.

    Args:
        level: Root log level.
        matplotlib_level: Matplotlib log level.

    See Also:
        Methods used:

            * :meth:`rics.utility.logs.basic_config`
            * :meth:`rics.utility.plotting.configure`
    """
    from rics.utility.logs import basic_config
    from rics.utility.plotting import configure

    basic_config(level=level, matplotlib_level=matplotlib_level)
    configure()
