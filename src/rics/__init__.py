"""My personal little ML engineering library."""
import logging
from os import getenv as _getenv

from ._just_the_way_i_like_it import configure_stuff

from .__version__ import __author__  # isort:skip
from .__version__ import __copyright__  # isort:skip
from .__version__ import __title__, __description__, __version__  # isort:skip

__all__ = [
    "configure_stuff",
    "__version__",  # Make MyPy happy
]

logging.getLogger(__name__).addHandler(logging.NullHandler())

if _getenv("JTWILI") == "true":  # pragma: no cover
    configure_stuff()
    print("Configured some things just the way I like it since JTWILI=true.")
