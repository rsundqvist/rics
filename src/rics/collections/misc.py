"""Miscellaneous utility methods for collections."""

import typing as _t
from collections.abc import Iterable as _Iterable

ArgType = _t.TypeVar("ArgType")
"""ArgType generic type."""


def as_list(arg: ArgType | _Iterable[ArgType] | None = None, excl_types: tuple[type[_t.Any]] = (str,)) -> list[ArgType]:
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
    if isinstance(arg, _Iterable) and not isinstance(arg, excl_types):
        return list(arg)
    else:
        return [arg]  # type: ignore[list-item]
