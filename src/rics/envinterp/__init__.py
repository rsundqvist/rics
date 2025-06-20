"""Legacy module.

Schedule:
    * ``rics==0.7.0``: Drop legacy module.

Please use :mod:`rics.env.interpolation` instead.
"""

from rics.env.interpolation import UnsetVariableError, Variable, replace_in_string

__all__ = ["UnsetVariableError", "Variable", "replace_in_string"]

import os
import warnings

if os.environ.get("SPHINX_BUILD") == "true":
    # Ugly fix for duplicate indexes.
    del __all__, UnsetVariableError, Variable, replace_in_string

warnings.warn(
    f"Package `{__package__}` is deprecated. Use `rics.env.interpolation` instead.",
    UserWarning,
    stacklevel=2,
)

del warnings
del os

# TODO(7.0.0): Remove this module
