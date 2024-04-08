"""Types used by this package."""

import os as _os
import typing as _t
from pathlib import Path as _Path

AnyPath: _t.TypeAlias = str | _os.PathLike[str] | _Path
"""Any path-like type; see :func:`~rics.paths.parse_any_path`."""
