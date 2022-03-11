import os
from enum import Enum
from typing import Literal, Union

PathLikeType = Union[str, bytes, os.PathLike]


class _NoDefault(Enum):
    """Internal type indicating that no default value should be used."""

    NO_DEFAULT = "<no-default>"

    def __str__(self) -> str:
        return "No default."


NoDefault = Literal[_NoDefault.NO_DEFAULT]
NO_DEFAULT = _NoDefault.NO_DEFAULT
