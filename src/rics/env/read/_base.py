import os
from collections.abc import Callable
from typing import NamedTuple, overload

from rics.types import T


@overload
def read_env(
    var: str,
    converter: Callable[[str], T],
    default: T,
    *,
    strict: bool = True,
    type_name: str | None = None,
    split: None = None,
    catch: tuple[type[Exception], ...] | None = None,
) -> T: ...


@overload
def read_env(
    var: str,
    converter: Callable[[str], T],
    default: T,
    *,
    strict: bool = True,
    type_name: str | None = None,
    split: str,
    catch: tuple[type[Exception], ...] | None = None,
) -> list[T]: ...


def read_env(
    var: str,
    converter: Callable[[str], T],
    default: T,
    *,
    strict: bool = True,
    type_name: str | None = None,
    split: str | None = None,
    catch: tuple[type[Exception], ...] | None = None,
) -> T | list[T]:
    """Read and convert an environment variable.

    Args:
        var: Variable to read.
        converter: A callable ``(str) -> T``, where the argument is the environment variable value.
        default: Default value to use when `var` is not set (or blank).
        strict: If ``False``, always fall back to `default` instead of raising.
        type_name: Used in error messages. Derive if ``None``.
        split: Character to split on. Returns ``list[T]`` when set.
        catch: Types to suppress when calling ``converter``. Default is ``(ValueError, TypeError)``.

    Returns:
        A ``T`` value, or a list thereof (if `split` is set).

    Raises:
        ValueError: If conversion fails.

    Notes:
        If the `variable` key is unset or the value is empty, the `default` value is always returned.
    """
    value = os.environ.get(var)
    if value is None:
        return [default] if split else default

    value = str(value).strip()  # Just in case; should already be a string.
    if value == "":
        return [default] if split else default

    if catch is None:
        catch = ValueError, TypeError

    cause: BaseException
    reason: str
    if split is None:
        try:
            return converter(value)
        except catch as exc:
            cause = exc
            reason = f": {exc}"
    else:
        result = _split(value.split(split), converter, catch)
        if isinstance(result, _ExceptionDetails):
            reason = f".\nNOTE: Failed at {var}[{result.idx}]={result.value!r}: {result.exception}"
            cause = result.exception
        else:
            return result

    if strict:
        if type_name is None:
            type_name = type(default).__name__
        if split:
            type_name = f"list[{type_name}]"
        msg = f"Bad value {var}={value!r}; not a valid `{type_name}` value" + reason
        raise ValueError(msg) from cause

    return [default] if split else default


class _ExceptionDetails(NamedTuple):
    exception: BaseException
    idx: int
    value: str


def _split(
    values: list[str],
    converter: Callable[[str], T],
    catch: tuple[type[BaseException], ...],
) -> list[T] | _ExceptionDetails:
    items = []
    for i, value in enumerate(values):
        stripped = value.strip()
        if stripped:
            try:
                result = converter(stripped)
                items.append(result)
            except catch as exc:
                return _ExceptionDetails(exc, i, stripped)

    return items
