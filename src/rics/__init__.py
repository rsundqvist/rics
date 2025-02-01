"""My personal little ML engineering library."""

import logging as _logging

from ._just_the_way_i_like_it import configure_stuff

__all__ = [
    "__version__",
    "configure_stuff",
]

__version__ = "5.0.1"

_logging.getLogger(__name__).addHandler(_logging.NullHandler())
