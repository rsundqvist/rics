"""My personal little ML engineering library."""
import logging

from .__version__ import __author__  # isort:skip
from .__version__ import __copyright__  # isort:skip
from .__version__ import __title__, __description__, __version__  # isort:skip

logging.getLogger(__name__).addHandler(logging.NullHandler())
