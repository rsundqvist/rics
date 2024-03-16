"""Miscellaneous utility methods for collections."""

from collections.abc import Iterable
from typing import Any, TypeVar

ArgType = TypeVar("ArgType")
"""ArgType generic type."""


def as_list(arg: ArgType | Iterable[ArgType] | None = None, excl_types: tuple[type[Any]] = (str,)) -> list[ArgType]:
    """Create a list or list-wrapping of `arg`.

    Args:
        arg: An object to name.
        excl_types: Iterable types that should be treated as single elements, such as strings.

    Returns:
        A list representation of `arg`.

    Notes:
        For all zero-length arguments, i.e. ``len(arg) == 0``, an empty list is returned.

    """
    # https://github.com/python/mypy/issues/10835
    if isinstance(arg, Iterable) and not isinstance(arg, excl_types):
        return list(arg)
    else:
        return [arg]  # type: ignore[list-item]
