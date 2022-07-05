"""Rics ML Engineering Library.

My personal little library. Written to help with common Machine Learning and Data Science tasks.
"""
import logging

from .__version__ import __author__  # isort:skip
from .__version__ import __copyright__  # isort:skip
from .__version__ import __title__, __description__, __version__  # isort:skip

logging.getLogger(__name__).addHandler(logging.NullHandler())
