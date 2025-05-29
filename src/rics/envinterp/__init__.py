"""Legacy module.

Schedule:
    * ``rics==0.6.0``: Emit :py:class:`DeprecationWarning` on import.
    * ``rics==0.7.0``: Drop legacy module.

Please use :mod:`rics.env.interpolation` instead.
"""

from rics.env.interpolation import UnsetVariableError, Variable, replace_in_string

__all__ = ["UnsetVariableError", "Variable", "replace_in_string"]

import os

if os.environ.get("SPHINX_BUILD") == "true":
    # Ugly fix for duplicate indexes.
    del __all__, UnsetVariableError, Variable, replace_in_string
del os

# TODO(6.0.0): Deprecate this module
# TODO(7.0.0): Remove this module
