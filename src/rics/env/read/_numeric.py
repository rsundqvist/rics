from typing import overload

from ._base import read_env


@overload
def read_int(var: str, default: int = 0, *, strict: bool = True, split: str) -> list[int]: ...
@overload
def read_int(var: str, default: int = 0, *, strict: bool = True, split: None = None) -> int: ...
def read_int(var: str, default: int = 0, *, strict: bool = True, split: str | None = None) -> int | list[int]:
    """Read ``int`` variable.

    Args:
        var: Variable to read.
        default: Default value to use when `var` is not set (or blank).
        strict: If ``False``, always fall back to `default` instead of raising.
        split: Character to split on. Returns ``list[int]`` when set.

    Returns:
        An ``int`` value, or a list thereof (if `split` is set).

    Examples:
        Basic usage.

        >>> import os
        >>> os.environ["MY_INT"] = "1"
        >>> read_int("MY_INT")
        1

        When using ``strict=False``, unmapped values are converted to the `default` instead of raising.

        >>> os.environ["MY_INT"] = "not-an-int"
        >>> read_int("MY_INT", strict=False)
        0

        Note that this includes passing ``float`` values, even if the decimal is zero.

        >>> os.environ["MY_INT"] = "0.0"
        >>> read_int("MY_INT", default=2019, strict=False)
        2019

        When using `split`, elements are cleaned individually and blank items are skipped.

        >>> os.environ["MY_INT_LIST"] = "0, 1, , 5"
        >>> read_int("MY_INT_LIST", split=",")
        [0, 1, 5]

        Conversion must succeed for all elements, or the `default` will be returned.
    """
    return read_env(var, int, default, strict=strict, split=split, catch=(ValueError,))


@overload
def read_float(var: str, default: float = 0.0, *, strict: bool = True, split: str) -> list[float]: ...
@overload
def read_float(var: str, default: float = 0.0, *, strict: bool = True, split: None = None) -> float: ...
def read_float(var: str, default: float = 0.0, *, strict: bool = True, split: str | None = None) -> float | list[float]:
    """Read ``float`` variable.

    Args:
        var: Variable to read.
        default: Default value to use when `var` is not set (or blank).
        strict: If ``False``, always fall back to `default` instead of raising.
        split: Character to split on. Returns ``list[float]`` when set.

    Returns:
        An ``float`` value, or a list thereof (if `split` is set).

    Examples:
        Basic usage.

        >>> import os
        >>> os.environ["MY_FLOAT"] = "1.0"
        >>> read_float("MY_FLOAT")
        1.0

        When using ``strict=False``, unmapped values are converted to the `default` instead of raising.

        >>> os.environ["MY_FLOAT"] = "not-a-float"
        >>> read_float("MY_FLOAT", strict=False)
        0.0

        When using `split`, elements are cleaned individually and blank items are skipped.

        >>> os.environ["MY_FLOAT_LIST"] = "0, 1.1, , 5"
        >>> read_float("MY_FLOAT_LIST", split=",")
        [0.0, 1.1, 5.0]

        Conversion must succeed for all elements, or the `default` will be returned.
    """
    return read_env(var, float, default, strict=strict, split=split, catch=(ValueError,))
