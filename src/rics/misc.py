"""Miscellaneous utility methods for Python applications."""
import inspect
import typing as _t
from importlib import import_module as _import_module
from pathlib import Path as _Path
from pprint import saferepr as _safe_repr
from types import ModuleType as _ModuleType

from ._internal_support import _local_or_remote
from ._internal_support.types import PathLikeType
from .envinterp import UnsetVariableError as _UnsetVariableError, Variable as _Variable


def interpolate_environment_variables(
    s: str,
    *,  # noqa: DAR401
    allow_nested: bool = True,
    allow_blank: bool = False,
) -> str:
    """Interpolate environment variables in a string `s`.

    This function replaces references to environment variables with the actual value of the variable, or a default if
    specified. The syntax is similar to Bash string interpolation; use ``${<var>}`` for mandatory variables, and
    ``${<var>:default}`` for optional variables.

    Args:
        s: A string in which to interpolate.
        allow_blank: If ``True``, allow variables to be set but empty.
        allow_nested: If ``True`` allow using another environment variable as the default value. This option will not
            verify whether the actual values are interpolation-strings.

    Returns:
        A copy of `s`, after environment variable interpolation.

    Raises:
        ValueError: If nested variables are discovered (only when ``allow_nested=False``).
        UnsetVariableError: If any required environment variables are unset or blank (only when ``allow_blank=False``).

    See Also:
        The :mod:`rics.envinterp` module, which this function wraps.
    """
    for var in _Variable.parse_string(s):
        if not allow_nested and (var.default and _Variable.parse_string(var.default)):
            raise ValueError(f"Nested variables forbidden since {allow_nested=}.")

        value = var.get_value(resolve_nested_defaults=allow_nested).strip()

        if not (allow_blank or value):
            raise _UnsetVariableError(var.name, f"Empty values forbidden since {allow_blank=}.")

        s = s.replace(var.full_match, value)
    return s


def get_by_full_name(name: str, default_module: _t.Union[str, _ModuleType] = None) -> _t.Any:
    """Combine :py:func:`~importlib.import_module` and :py:func:`getattr` to retrieve items by name.

    Args:
        name: A name or fully qualified name.
        default_module: A namespace to search if `name` is not fully qualified (contains no ``'.'``-characters).

    Returns:
        An object with the fully qualified name `name`.

    Raises:
        ValueError: If `name` does not contain any dots and ``default_module=None``.

    Examples:
        Retrieving a ``numpy`` function by name.

        >>> get_by_full_name("numpy.isnan")
        <ufunc 'isnan'>

        Falling back to builtins.

        >>> get_by_full_name("int", default_module="builtins")
        <class 'int'>
    """
    if "." in name:
        module_name, _, member = name.rpartition(".")
        module = _import_module(module_name)
    else:
        if not default_module:
            raise ValueError("Names must be fully qualified when no default module is given.")  # pragma: no cover
        module = _import_module(default_module) if isinstance(default_module, str) else default_module
        member = name

    return getattr(module, member)


def get_public_module(obj: _t.Any, resolve_reexport: bool = False, include_name: bool = False) -> str:
    """Get the public module of `obj`.

    Args:
        obj: An object to resolve a public module for.
        resolve_reexport: If ``True``, traverse the module hierarchy and look for the earliest where `obj` is
            reexported. This may be expensive.
        include_name: If ``True``, include the name of `obj` reexported from a parent module. The first instance found
            will be used if `obj` is reexported multiple times.

    Returns:
        Public module of `obj`.

    Examples:
        Public module of ``pandas.DataFrame``.

        >>> from pandas import DataFrame as obj
        >>> get_public_module(obj)
        'pandas.core.frame'
        >>> get_public_module(obj, resolve_reexport=True)
        'pandas'
        >>> get_public_module(obj, resolve_reexport=True, include_name=True)
        'pandas.DataFrame'

    Raises:
        ValueError: If `include_name` is given without `resolve_reexport`.

    See Also:
        The analogous :func:`get_by_full_name`-function.
    """
    if include_name and not resolve_reexport:
        raise ValueError(f"Cannot combine {include_name=} with {resolve_reexport=}.")

    parts = []
    for part in obj.__module__.split("."):
        if part[0] == "_":
            break
        parts.append(part)

    if resolve_reexport:
        obj_id = id(obj)

        for i in range(1, len(parts) + 1):
            module = _import_module(".".join(parts[:i]))
            for name, _ in inspect.getmembers(module, predicate=lambda member: id(member) == obj_id):
                parts = parts[:i]
                if include_name:
                    parts.append(name)
                return ".".join(parts)

    return ".".join(parts)


def tname(
    arg: _t.Optional[_t.Union[_t.Type[_t.Any], _t.Any]],
    prefix_classname: bool = False,
    attrs: _t.Optional[_t.Union[str, _t.Iterable[str]]] = "func",
) -> str:
    """Get name of method or class.

    Args:
        arg: Something get a name for.
        prefix_classname: If ``True``, prepend the class name if `arg` belongs to a class.
        attrs: Attribute names to search for wrapped functions. The default, `'func'`, is the name used by the built-in
            :py:func:`functools.partial` wrapper. May cause infinite recursion.

    Returns:
        A name for `arg`.

    Raises:
        ValueError: If no name could be derived for `arg`.
    """
    if arg is None:
        return "None"

    if attrs:
        from rics.collections.misc import as_list

        attrs = as_list(attrs)
        for attr in attrs:
            wrapped = getattr(arg, attr, arg)
            if wrapped is arg:
                break
            return tname(wrapped, prefix_classname=prefix_classname, attrs=attrs)

    if hasattr(arg, "__qualname__"):
        return arg.__qualname__ if prefix_classname else arg.__name__
    if hasattr(arg, "__name__"):
        return arg.__name__
    if hasattr(arg, "fget"):
        # Instance-level properties accessed using the class.
        return tname(arg.fget, prefix_classname=prefix_classname)
    if hasattr(arg, "__class__"):
        return arg.__class__.__name__
    else:
        raise ValueError(f"Could not derive a name for {arg=}.")  # pragma: no cover


def format_kwargs(kwargs: _t.Dict[str, _t.Any], *, max_value_length: int = None) -> str:
    """Format keyword arguments.

    Args:
        kwargs: Arguments to format.
        max_value_length: If given, replace ``repr(value)`` with ``tname(value)`` if repr is longer than
            `max_value_length` characters.

    Returns:
        A string on the form `'key0=repr(value0), key1=repr(value1)'`.

    Raises:
        ValueError: For keys in `kwargs` that are not valid Python argument names.

    Examples:
        >>> format_kwargs({'an_int': 1, 'a_string': 'Hello!'})
        "an_int=1, a_string='Hello!'"
    """
    invalid = [k for k in kwargs if not k.isidentifier()]
    if invalid:
        raise ValueError(f"Got {len(invalid)} invalid identifiers: {invalid}.")

    def repr_value(value: _t.Any) -> str:
        value_repr = _safe_repr(value)
        if max_value_length is None or len(value_repr) <= max_value_length:
            return value_repr
        return tname(value)

    return ", ".join(f"{k}={repr_value(v)}" for k, v in kwargs.items())


def get_local_or_remote(
    file: PathLikeType,
    remote_root: PathLikeType,
    local_root: PathLikeType = ".",
    force: bool = False,
    postprocessor: _t.Callable[[str], _t.Any] = None,
    show_progress: bool = _local_or_remote.TQDM_INSTALLED,
) -> _Path:
    r"""Retrieve the path of a local file, downloading it if needed.

    If `file` is not available at the local root path, it will be downloaded using `requests.get`_. A postprocessor may
    be given in which case the name of the final file will be ``local_root/<name-of-postprocessor>/file``. Removing
    a raw local file (i.e. ``local_root/file``) will invalidate postprocessed files as well.

    Args:
        file: A file to retrieve or download.
        remote_root: Remote URL where the data may be retrieved using ``requests.get``.
        local_root: Local directory where the file may be cached.
        force: If ``True``, always download and apply processing (if applicable). Existing files will be overwritten.
        postprocessor: A function which takes a single argument `input_path` and returns a pickleable type.
        show_progress: If ``True``, show a progress bar. Requires the `tqdm`_ package.

    Returns:
        An absolute path to the data.

    Raises:
        ValueError: If local root path does not exist or is not a directory.
        ValueError: If the local file does not exist and ``remote=None``.
        ModuleNotFoundError: If the ``tqdm`` package is not installed but ``show_progress=True``.

    Examples:
        Fetch the Title Basics table (a CSV file) of the `IMDb dataset`_.

        >>> from rics.misc import get_local_or_remote
        >>> import pandas as pd
        >>>
        >>> file = "name.basics.tsv.gz"
        >>> local_root = "my-data"  # default = "."
        >>> remote_root = "https://datasets.imdbws.com"
        >>> path = get_local_or_remote(file, remote_root, local_root, show_progress=True) # doctest: +SKIP
        >>> pd.read_csv(path, sep="\t").shape # doctest: +SKIP
        https://datasets.imdbws.com/name.basics.tsv.gz: 100%|██████████| 214M/214M [00:05<00:00, 39.3MiB/s]
        (11453719, 6)

        We had download `name.basics.tsv.gz` the first time, but ``get_local_or_remote`` returns immediately the second
        time it is called. Fetching can be forced using ``force_remote=True``.

        >>> path = get_local_or_remote(file, remote_root, local_root, show_progress=True) # doctest: +SKIP
        >>> pd.read_csv(path, sep="\t").shape # doctest: +SKIP
        (11453719, 6)

    .. _IMDb dataset:
        https://www.imdb.com/interfaces/
    .. _requests.get:
        https://2.python-requests.org/en/master/api/#requests.get
    .. _tqdm:
        https://pypi.org/project/tqdm/
    """
    return _local_or_remote.get_local_or_remote(
        file=file,
        local_root=local_root,
        remote_root=remote_root,
        force=force,
        postprocessor=postprocessor,
        show_progress=show_progress,
    )


def serializable(obj: _t.Any) -> bool:
    """Check if `obj` is serializable using Pickle.

    Serializes to memory for speed.

    Args:
        obj: An object to attempt to serialize.

    Returns:
        ``True`` if `obj` was pickled without issues.
    """
    import io
    import pickle  # noqa: S403

    bio = io.BytesIO()
    try:
        pickle.dump(obj, bio)
        return True
    except Exception:  # noqa: B902
        return False
