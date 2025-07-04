"""My personal little ML engineering library.

Environment variables
---------------------
.. envvar:: JTWILI

    Set ``JTWILI=true`` to disable the warning emitted by :func:`rics.configure_stuff`.


"""

import logging as _logging

from ._just_the_way_i_like_it import configure_stuff

__all__ = [
    "__version__",
    "configure_stuff",
]

__version__ = "6.0.1.dev1"

_logging.getLogger(__name__).addHandler(_logging.NullHandler())
