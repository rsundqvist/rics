"""Read environment variables as specific types.

To read ``typing.Literal`` values, use :meth:`rics.types.LiteralHelper.read_env` instead.
"""

from ._base import read_env
from ._bool import read_bool
from ._enum import read_enum
from ._numeric import read_float, read_int
from ._str import read_str

__all__ = [
    "read_bool",
    "read_enum",
    "read_env",
    "read_float",
    "read_int",
    "read_str",
]
