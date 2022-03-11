"""Rics ML Engineering Library.

My little library written help with common Machine Learning and Data Science tasks.

Highlights:
    * Various utility modules in the :mod:`rics.utility` package.
    * Configurable mapping in the :mod:`rics.mapping` package.
    * Flexible translation of IDs in :mod:`rics.translation` package suite.
"""
import logging

from .__version__ import __author__  # isort:skip
from .__version__ import __copyright__  # isort:skip
from .__version__ import __title__, __description__, __version__  # isort:skip

logging.getLogger(__name__).addHandler(logging.NullHandler())
