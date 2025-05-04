from typing import overload

from ._base import read_env


@overload
def read_str(var: str, default: str = "", *, strict: bool = True, split: str) -> list[str]: ...
@overload
def read_str(var: str, default: str = "", *, strict: bool = True, split: None = None) -> str: ...
def read_str(var: str, default: str = "", *, strict: bool = True, split: str | None = None) -> str | list[str]:
    """Read ``str`` variable.

    Args:
        var: Variable to read.
        default: Default value to use when `var` is not set (or blank).
        strict: If ``False``, always fall back to `default` instead of raising.
        split: Character to split on. Returns ``list[str]`` when set.

    Returns:
        An ``str`` value, or a list thereof (if `split` is set).

    Examples:
        Basic usage.

        >>> import os
        >>> os.environ["MY_STR"] = "  foo "
        >>> read_str("MY_STR")
        'foo'

        Input is stripped and cleaned, returning bare strings. Empty items are discarded when using `split`.

        >>> os.environ["MY_STR_LIST"] = "  foo, , bar "
        >>> read_str("MY_STR_LIST", split=",")
        ['foo', 'bar']

        This means that input such as ``',  , , '`` will return an empty list.
    """
    return read_env(var, str.strip, default, strict=strict, split=split)
