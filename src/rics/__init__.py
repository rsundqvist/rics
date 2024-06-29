"""My personal little ML engineering library."""

import logging as _logging

from ._just_the_way_i_like_it import configure_stuff

__all__ = [
    "configure_stuff",
    "__version__",
]

__version__ = "4.1.1"

_logging.getLogger(__name__).addHandler(_logging.NullHandler())
