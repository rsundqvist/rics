"""Utility modules."""

from rics.utility import collections, logs, misc, strings
from rics.utility._just_the_way_i_like_it import configure_stuff

__all__ = ["configure_stuff", "collections", "logs", "misc", "strings"]

try:
    from rics.utility import plotting

    __all__ += ["plotting"]
except ModuleNotFoundError:
    pass
