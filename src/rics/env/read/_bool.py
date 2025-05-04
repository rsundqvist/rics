from typing import overload

from rics.strings import str_as_bool

from ._base import read_env


@overload
def read_bool(var: str, default: bool = False, *, strict: bool = True, split: str) -> list[bool]: ...
@overload
def read_bool(var: str, default: bool = False, *, strict: bool = True, split: None = None) -> bool: ...
def read_bool(var: str, default: bool = False, *, strict: bool = True, split: str | None = None) -> bool | list[bool]:
    """Read ``bool`` variable.

    Args:
        var: Variable to read.
        default: Default value to use when `var` is not set (or blank).
        strict: If ``False``, always fall back to `default` instead of raising.
        split: Character to split on. Returns ``list[bool]`` when set.

    Returns:
        A ``bool`` value, or a list thereof (if `split` is set).

    Notes:
        See :func:`~rics.strings.str_as_bool` for value mapping.

    Examples:
        Basic usage.

        >>> import os
        >>> os.environ["MY_BOOL"] = "true"
        >>> read_bool("MY_BOOL")
        True

        >>> os.environ["MY_BOOL"] = "0"
        >>> read_bool("MY_BOOL")
        False

        When using ``strict=False``, unmapped values are converted to the `default` instead of raising.

        >>> os.environ["MY_BOOL"] = "not-a-bool"
        >>> read_bool("MY_BOOL", default=True, strict=False)
        True

        When using `split`, elements are cleaned individually and blank items are skipped.

        >>> os.environ["MY_BOOL_LIST"] = "true, 0, no, yes, enable,, false"
        >>> read_bool("MY_BOOL_LIST", split=",")
        [True, False, False, True, True, False]

        Conversion (see :attr:`~rics.strings.str_as_bool`) must succeed for all elements, or the `default` will be
        returned.
    """
    return read_env(var, str_as_bool, default, strict=strict, split=split)
