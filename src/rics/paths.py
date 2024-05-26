"""Utility methods for working with paths and filesystems."""

import typing as _t
from pathlib import Path as _Path

from rics.types import AnyPath as _AnyPath

AnyPath = _AnyPath
"""Reexport of :attr:`rics.types.AnyPath`."""
PathT = _t.TypeVar("PathT", str, _Path)  # Would be nice to allow Any or a bound
"""A specific path-like type."""
PathPostprocessor = _t.Callable[[PathT], PathT | bool | None]


def any_path_to_str(
    path: _AnyPath,
    *,
    postprocessor: PathPostprocessor[str] | None = None,
) -> str:
    """Docstring is generated."""
    return parse_any_path(path, cls=str, postprocessor=postprocessor)


def any_path_to_path(
    path: _AnyPath,
    *,
    postprocessor: PathPostprocessor[_Path] | None = None,
) -> _Path:
    """Docstring is generated."""
    return parse_any_path(path, cls=_Path, postprocessor=postprocessor)


def parse_any_path(
    path: _AnyPath,
    *,
    cls: type[PathT],
    postprocessor: PathPostprocessor[PathT] | None = None,
) -> PathT:
    """Docstring is generated."""
    converted_path = _convert_path(path, cls=cls)

    if postprocessor is not None:
        result = postprocessor(converted_path)
        if isinstance(result, cls):
            converted_path = result
        elif result is None or result is True:
            pass  # postprocessor was a validation function
        elif result is False:
            from rics.misc import tname

            msg = f"Validator {tname(postprocessor, prefix_classname=True)}({converted_path!r}) returned False."
            raise ValueError(msg)
        else:
            from rics.misc import tname

            pretty_actual = f"`{tname(result)}`"
            pretty_expected = f"({tname(cls)} | bool | None)"
            pretty_pp = f"{tname(postprocessor)}({converted_path!r})"
            msg = f"Postprocessor {pretty_pp} returned {result=} of type {pretty_actual}; expected={pretty_expected}."
            raise TypeError(msg)

    return converted_path


def _convert_path(path: _AnyPath, *, cls: type[PathT]) -> PathT:
    if isinstance(path, cls):
        return path

    if issubclass(cls, str):
        return cls(path)

    if issubclass(cls, _Path) and isinstance(path, str):
        return cls(path)

    try:
        return cls(str(path))
    except Exception as e:
        msg = f"Cannot convert {path=} from type(path)=`{type(path).__name__}` to cls=`{cls.__name__}`."
        raise TypeError(msg) from e


def _set_path_func_docstring(func: _t.Any, cls: str | type[_t.Any], tail: str = "") -> None:
    args = {"path": "Any :class:`path-like <rics.paths.AnyPath>` type."}

    if isinstance(cls, type):  # Specialization
        cls = cls.__name__

        equivalent_to = f"""Equivalent to :func:`parse_any_path(path, cls={cls}) <.parse_any_path>`."""
        args["postprocessor"] = f"A callable ``({cls}) -> {cls} | None``."

        cls = f"``{cls}``"
    else:  # Base function
        equivalent_to = ""
        args["cls"] = "Desired output type; typically one of :py:class:`str` | :py:class:`pathlib.Path`."
        args["postprocessor"] = "A callable ``(PathT) -> PathT | bool | None``."

    args["postprocessor"] += " Returns the post-processed value if `postprocessor` does not return ``None | bool``."

    args_str = "\n        ".join(f"{arg}: {docstring}" for arg, docstring in args.items())
    docstring = f"""Convert a path of any type to {cls}.

    {equivalent_to}

    Args:
        {args_str}

    Returns:
        A `path` of type {cls}.

    {tail}
    """

    func.__doc__ = docstring


_set_path_func_docstring(
    parse_any_path,
    cls="of type `cls`",
    tail="""Raises:
        TypeError: If the `postprocessor` returns an invalid type.
        ValueError: If the `postprocessor` returns ``False``.

    Postprocessor return types:
        * ``None``: Validator. Should raise if there's an issue.
        * ``bool``: Validator, e.g. :meth:`~pathlib.Path.is_dir`. Raises a ``ValueError`` if the
          function returns ``False``.
        * ``PathT``: Postprocessor, e.g. :meth:`~pathlib.Path.absolute`. Result is returned as-is.

    Examples:
        >>> from pathlib import Path
        >>> parse_any_path("/home/dev/", cls=Path)
        PosixPath('/home/dev')

        >>> parse_any_path(Path("/home/dev/"), cls=Path)
        PosixPath('/home/dev')

    See Also:
        * :func:`any_path_to_str`: Alias of ``parse_any_path(cls=str)``
        * :func:`any_path_to_path`: Alias of ``parse_any_path(cls=pathlib.Path)``
""",
)
_set_path_func_docstring(any_path_to_str, cls=str)
_set_path_func_docstring(any_path_to_path, cls=_Path)
