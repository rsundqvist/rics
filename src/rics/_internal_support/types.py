import os
from enum import Enum
from typing import Literal, Union

PathLikeType = Union[str, os.PathLike]  # type: ignore[type-arg]


class _NoDefault(Enum):
    """Internal type indicating that no default value should be used."""

    NO_DEFAULT = "<no-default>"


NoDefault = Literal[_NoDefault.NO_DEFAULT]
NO_DEFAULT = _NoDefault.NO_DEFAULT
