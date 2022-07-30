"""Miscellaneous utility methods for collections."""

from typing import Iterable, List, Tuple, Type, TypeVar, Union

ArgType = TypeVar("ArgType")
"""ArgType generic type."""


def as_list(arg: Union[ArgType, Iterable[ArgType]] = None, excl_types: Tuple[Type] = (str,)) -> List[ArgType]:
    """Create a list or list-wrapping of `arg`.

    Args:
        arg: Input data..
        excl_types: Iterable types that should be treated as single elements, such as strings.

    Returns:
        A list representation of `arg`.

    Notes:
        For all zero-length arguments, i.e. ``len(arg) == 0``, an empty list is returned.
    """
    # https://github.com/python/mypy/issues/10835
    return list(arg) if isinstance(arg, Iterable) and not isinstance(arg, excl_types) else [arg]  # type: ignore
