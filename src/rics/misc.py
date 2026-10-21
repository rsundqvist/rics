"""Miscellaneous utility methods for Python applications."""

import typing as _t
from importlib import import_module as _import_module
from pathlib import Path as _Path
from pprint import saferepr as _safe_repr
from types import MethodType as _MethodType
from types import ModuleType as _ModuleType

from . import paths as _paths
from .types import AnyPath as _AnyPath


def interpolate_environment_variables(
    s: str,
    *,
    allow_nested: bool = True,
    allow_blank: bool = False,
) -> str:
    """Alias of :func:`rics.env.interpolation.replace_in_string`."""
    import warnings

    from rics.env.interpolation import replace_in_string

    warnings.warn(
        "Function `interpolate_environment_variables()` is deprecated. "
        "Use `rics.env.interpolation.replace_in_string` instead.",
        UserWarning,
        stacklevel=2,
    )
    # TODO(7.0.0): Remove this function

    return replace_in_string(s, allow_nested=allow_nested, allow_blank=allow_blank)


GBFNReturnType = _t.TypeVar("GBFNReturnType")
"""Output type for :func:`get_by_full_name` when using one of `instance_of` and `subclass_of`."""


@_t.overload
def get_by_full_name(
    name: str,
    default_module: str | _ModuleType | object = ...,
    *,
    instance_of: _t.Literal[None] = None,
    subclass_of: _t.Literal[None] = None,
) -> _t.Any:
    pass


@_t.overload
def get_by_full_name(
    name: str,
    default_module: str | _ModuleType | object = ...,
    *,
    instance_of: type[GBFNReturnType],
    subclass_of: _t.Literal[None] = None,
) -> GBFNReturnType:
    pass


@_t.overload
def get_by_full_name(
    name: str,
    default_module: str | _ModuleType | object = ...,
    *,
    instance_of: _t.Literal[None] = None,
    subclass_of: type[GBFNReturnType],
) -> type[GBFNReturnType]:
    pass


def get_by_full_name(
    name: str,
    default_module: str | _ModuleType | object | None = None,
    *,
    instance_of: type[GBFNReturnType] | None = None,
    subclass_of: type[GBFNReturnType] | None = None,
) -> _t.Any:
    """Combine :py:func:`importlib.import_module` and :py:func:`getattr` to retrieve items by name.

    You may retrieve top-level module members such as classes by adding the class name after the module path (e.g.
    ``logging.Logger``). The member may also be specified using the ``':'``-syntax, e.g. ``logging:Logger``. The
    ``':'``-syntax also supports retrieving object members e.g. ``logging:Logger.info``. This is not possible using the
    dot-based syntax since ``logging.Logger`` cannot be imported by the ``importlib.import_module`` function.

    Args:
        name: A name or fully qualified name.
        default_module: A namespace to search if `name` does not contain any ``'.'`` or ``':'`` characters.
        instance_of: If given, perform :py:func:`isinstance` check on `name`.
        subclass_of: If given, perform :py:func:`issubclass` check on `name`.

    Returns:
        The object specified by `name`.

    Raises:
        ValueError: If `name` does not contain any dots and ``default_module=None``.
        ValueError: If both `instance_of` and `subclass_of` are given.
        TypeError: If an ``isinstance`` or ``issubclass`` check fails.

    Examples:
        Retrieving a ``numpy`` function by name.

        >>> get_by_full_name("numpy.isnan")
        <ufunc 'isnan'>

        Validating the return type. In the example below, we ensure that ``logging.INFO`` really is an ``int``, and that
        the :py:class:`logging.Logger` class inherits from ``logging.Filterer``.

        >>> import logging
        >>> get_by_full_name("logging.INFO", instance_of=int)
        20
        >>> get_by_full_name("logging.Logger", subclass_of=logging.Filterer)
        <class 'logging.Logger'>

        Default namespaces may be specified using the `default_module` keyword argument.

        >>> get_by_full_name("Logger", default_module="logging")
        <class 'logging.Logger'>

        The default namespace doesn't have to be a module.

        >>> get_by_full_name("info", default_module="logging.Logger").__qualname__
        'Logger.info'

        To retrieve an attribute of anything other than a module (e.g. a class member), you must use the ``:``-syntax to
        separate the module path from the attribute path.

        >>> get_by_full_name("logging:Logger.info").__qualname__
        'Logger.info'

        When using this syntax, the path to the left of the separator must be a valid module path.

    See Also:
        The reverse operation, :func:`get_public_module`.
    """
    name = name.strip()
    if name == "":
        msg = "Name must not be empty."
        raise ValueError(msg)

    if not (instance_of is None or subclass_of is None):
        msg = f"At least one of ({instance_of=}, {subclass_of=}) must be None."
        raise ValueError(msg)

    obj = _get_by_full_name(name, default_module=default_module)

    if instance_of is not None:  # noqa: SIM102 # See https://github.com/nedbat/coveragepy/issues/509
        if not isinstance(obj, instance_of):
            msg = f"Expected an instance of {instance_of.__name__}, but got {obj=}."
            raise TypeError(msg)

    if subclass_of is not None:
        reason = ""
        try:
            if not issubclass(obj, subclass_of):
                reason = "does not inherit from {subclass_of}"
        except TypeError as e:
            if "must be a class" in str(e):
                reason = "is not a class"
            else:
                raise
        if reason:
            pretty = tname(subclass_of, prefix_classname=True)
            reason = reason.format(subclass_of=pretty)
            msg = f"Expected a subclass of {pretty}, but {obj=} {reason}."
            raise TypeError(msg)

    return obj


def _get_by_full_name(name: str, *, default_module: str | object | None = None) -> _t.Any:
    path: list[str]

    force_default_module = name[0] == ":"

    if force_default_module and not default_module:
        msg = f"Cannot use {name=} (with leading ':') without a default module."
        raise ValueError(msg)

    root: object
    if ":" in name and not force_default_module:
        module_name, _, member = name.rpartition(":")
        root = _import_module(module_name)
        path = member.split(".")
    elif "." in name and not force_default_module:
        module_name, _, member = name.rpartition(".")
        root = _import_module(module_name)
        path = [member]
    else:
        if not default_module:
            msg = "Name must be fully qualified when no default module is given."
            raise ValueError(msg)

        if isinstance(default_module, str):
            if ":" in default_module or "." in default_module:
                root = _get_by_full_name(default_module)
            else:
                root = _import_module(default_module)
        else:
            root = default_module

        path = name.removeprefix(":").split(".")

    obj = root
    for attr in path:
        obj = getattr(obj, attr)
    return obj


def get_public_module(obj: _t.Any, resolve_reexport: bool = False, include_name: bool = False) -> str:
    """Get the public module of `obj`.

    Args:
        obj: An object to resolve a public module for.
        resolve_reexport: If ``True``, traverse the module hierarchy and look for the earliest where `obj` is
            reexported. This may be expensive.
        include_name: If ``True``, include the name of `obj` reexported from a parent module. The first instance found
            will be used if `obj` is reexported multiple times. If `obj` is not found in any public module, the name is
            ``f"{obj.__module__}.{obj.__qualname__}"``. Objects without a ``__qualname__`` (e.g. instances) get no
            name at all; the result is then the public part of ``obj.__module__``, which need not contain `obj`.

    Returns:
        Public module of `obj`.

    Examples:
        Public module of ``pandas.DataFrame`` (legacy versions).

        >>> from pandas import DataFrame as obj
        >>> get_public_module(obj)  # doctest: +SKIP
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
    # TODO(6.3.0): This does two jobs. Split into a public-module lookup and a `get_full_name` that is the strict
    #  inverse of get_by_full_name (raising when there is no importable path), so neither has to compromise for the
    #  other. Deprecate `include_name`.
    import inspect

    if include_name and not resolve_reexport:
        raise ValueError(f"Cannot combine {include_name=} with {resolve_reexport=}.")

    module_name = obj.__module__
    assert isinstance(module_name, str), f"{module_name=}"  # noqa: S101

    parts = []
    for part in module_name.split("."):
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

        # TODO(7.0.0): Emit `module:qualname` so that dotted qualnames (e.g. methods) resolve with get_by_full_name.
        if include_name and isinstance(qualname := getattr(obj, "__qualname__", None), str):
            return f"{module_name}.{qualname}"

    if not parts:
        return module_name

    return ".".join(parts)


def tname(
    arg: type[_t.Any] | _t.Any | None,
    prefix_classname: bool = False,
    attrs: str | _t.Iterable[str] | None = "func",
    include_module: bool = False,
) -> str:
    """Get name of method or class.

    Meant for display, e.g. in logs and error messages; the result may not resolve back to `arg`. Use
    :func:`get_public_module` with ``include_name=True`` and :func:`get_by_full_name` to look an object up by name.

    Args:
        arg: Something get a name for.
        prefix_classname: If ``True``, prepend the class name if `arg` belongs to a class. Builtins bound to a module or
            an instance get their own type name instead, e.g. ``'builtin_function_or_method.len'`` for ``len``.
        attrs: Attribute names to search for wrapped functions. The default, `'func'`, is the name used by the built-in
            :py:func:`functools.partial` wrapper. Any attribute with one of these names is followed, including
            methods, properties and values made up by ``__getattr__``.
        include_module: If ``True``, prepend the public module (see :func:`get_public_module`).

    Returns:
        A name for `arg`.

    Raises:
        ValueError: If no name could be derived for `arg`.
        RecursionError: If unwrapping `arg` does not terminate, e.g. due to a wrapper cycle.

    """
    # TODO(6.3.0): Scope creep; this is a display name with unwrapping and module lookup bolted on. Consider splitting
    #  into `unwrap(obj, attrs)` and a `display_name(obj, prefix_classname, include_module)`.
    if attrs:
        attrs = [attrs] if isinstance(attrs, str) else [*attrs]
        arg = _unwrap(arg, attrs)

    if arg is None:
        return "None"

    name = _get_name(arg, prefix_classname)
    return f"{_get_module(arg)}.{name}" if include_module else name


def _unwrap(arg: type[_t.Any] | _t.Any | None, attrs: list[str]) -> type[_t.Any] | _t.Any | None:
    sentinel = object()
    original = arg

    # TODO(7.0.0): Detect cycles with a `seen` id-to-object dict (holding refs so ids aren't reused) and raise
    #  ValueError like inspect.unwrap; keep `max_depth` for runaway __getattr__. New exception type, hence not 6.x.

    # Real chains are a few levels deep (nested partials flatten themselves). This only bounds cycles and runaway
    # __getattr__, e.g. a Mock creating (and keeping) a new child on every probe.
    max_depth = 100
    for _ in range(max_depth):
        for attr in attrs:
            # shortcut: any matching attr is followed (also by the `fget` probes), even properties and __getattr__ values,
            #  so pd.Series([1], index=["func"]) names as 'int64'. Fine for display; heuristics must be maintained.
            wrapped = getattr(arg, attr, sentinel)
            if wrapped is not sentinel and wrapped is not arg:
                break
        else:
            return arg

        arg = wrapped

    # Types only; repr() may raise or be huge.
    msg = f"Gave up unwrapping {type(original).__qualname__} with {attrs=} after {max_depth} levels; last {type(arg).__qualname__}."
    raise RecursionError(msg)


def _get_name(arg: type[_t.Any] | _t.Any, prefix_classname: bool) -> str:
    if prefix_classname and hasattr(arg, "__self__"):
        arg_self = arg.__self__
        if isinstance(arg_self, type):
            cls_name = arg_self.__name__
        elif isinstance(arg, _MethodType):
            cls_name = type(arg_self).__qualname__
        else:
            # TODO(6.3.0): Name builtins as `len` / `list.append`. MultiCaseTimer derives candidate labels from this, so
            #  it must first handle the collisions that creates, e.g. `[sum, np.sum]` and `[math.floor, np.floor]`. This
            #  also fixes include_module paths like `math.builtin_function_or_method.floor`, which name no real object.
            #  Candidate labels change for users (a lone `len` becomes `'len'`): add a "Changed" changelog entry. Also
            #  drop the builtin sentence from the `prefix_classname` docstring and update the expectations in
            #  test_builtin_prefix_classname, test_pybind11 and test_builtin_candidate_labels. Then restore these:
            #  # Builtins: module-level ones like `len` have a `__module__`, methods like `[].append` don't.
            #  return arg.__name__ if isinstance(getattr(arg, "__module__", None), str) else arg.__qualname__
            cls_name = type(arg).__name__
        return f"{cls_name}.{arg.__name__}"

    if hasattr(arg, "__qualname__"):
        return arg.__qualname__ if prefix_classname else arg.__name__
    if hasattr(arg, "fget"):
        # Instance-level properties accessed using the class.
        return tname(arg.fget, prefix_classname=prefix_classname)
    if hasattr(arg, "__name__"):
        return arg.__name__
    if hasattr(arg, "__class__"):
        return arg.__class__.__qualname__ if prefix_classname else arg.__class__.__name__
    else:
        raise ValueError(f"Could not derive a name for {arg=}.")  # pragma: no cover


def _get_module(arg: type[_t.Any] | _t.Any) -> str:
    if hasattr(arg, "fget"):
        # Instance-level properties accessed using the class.
        obj = arg.fget
    elif isinstance(arg, _MethodType) or not isinstance(getattr(arg, "__module__", None), str):
        # Builtin functions with a `__module__` are module-level; their `__self__` may be the module or something
        # unimportable (pybind11).
        obj = getattr(arg, "__self__", arg)
    elif hasattr(arg, "__name__"):
        obj = arg
    else:
        obj = type(arg)

    if not isinstance(getattr(obj, "__module__", None), str):
        obj = type(obj)  # E.g. the list of `[].append`.

    return get_public_module(obj, include_name=False, resolve_reexport=True)


def format_kwargs(kwargs: _t.Mapping[str, _t.Any], *, max_value_length: int = 80) -> str:
    """Format keyword arguments.

    .. warning::

       This function will be removed in a future version. Use :func:`.strings.format_kwargs` instead.

    Args:
        kwargs: Arguments to format.
        max_value_length: Replace value with class name above this limit. 0=no limit.

    Returns:
        A string on the form `'key0=repr(value0), key1=repr(value1)'`.

    Raises:
        ValueError: For keys in `kwargs` that are not valid Python argument names.

    Examples:
        Basic usage.

        >>> format_kwargs({"an_int": 1, "a_string": "Hello!"})
        "an_int=1, a_string='Hello!'"
    """
    # TODO(7.0.0): deprecate in favor of string.format_kwargs() + update docstring ::warning

    invalid = [k for k in kwargs if not k.isidentifier()]
    if invalid:
        raise ValueError(f"Got {len(invalid)} invalid identifiers: {invalid}.")

    def repr_value(value: _t.Any) -> str:
        value_repr = _safe_repr(value)
        if max_value_length <= 0 or len(value_repr) <= max_value_length:
            return value_repr
        return tname(value)

    return ", ".join(f"{k}={repr_value(v)}" for k, v in kwargs.items())


def get_local_or_remote(
    file: _AnyPath,
    *,
    remote_root: _AnyPath,
    local_root: _AnyPath = ".",
    force: bool = False,
    postprocessor: _t.Callable[[str], _t.Any] | None = None,
    show_progress: bool | None = None,
) -> _Path:
    r"""Retrieve the path of a local file, downloading it if needed.

    If `file` is not available at the local root path, it will be downloaded using `requests`_. An HTTP error status
    raises ``requests.HTTPError`` instead of writing the error page to the local file. A postprocessor may be given, in
    which case the name of the final file will be ``local_root/<name-of-postprocessor>/file``. Removing a raw local
    file (i.e. ``local_root/file``) will invalidate postprocessed files as well.

    Args:
        file: A file to retrieve or download.
        remote_root: Remote URL where the data may be retrieved using ``requests.get``.
        local_root: Local directory where the file may be cached.
        force: If ``True``, always download and apply processing (if applicable). Existing files will be overwritten.
        postprocessor: A function which takes a single argument `input_path` and returns a pickleable type.
        show_progress: If ``True``, show a progress bar. Requires the `tqdm`_ package. If ``None``, use only if TQDM
            is installed.

    Returns:
        An absolute path to the data.

    Raises:
        ValueError: If local root path does not exist or is not a directory.
        ModuleNotFoundError: If the ``tqdm`` package is not installed but ``show_progress=True``.
        requests.HTTPError: If the server responds with an HTTP error status.

    Examples:
        Fetch the Name Basics table (a TSV file) of the `IMDb dataset`_.

        >>> from rics.misc import get_local_or_remote
        >>> import pandas as pd
        >>>
        >>> file = "name.basics.tsv.gz"
        >>> local_root = "my-data"  # default = "."
        >>> remote_root = "https://datasets.imdbws.com"
        >>> path = get_local_or_remote(
        ...     file, remote_root=remote_root, local_root=local_root, show_progress=True
        ... )  # doctest: +SKIP
        >>> pd.read_csv(path, sep="\t").shape  # doctest: +SKIP
        https://datasets.imdbws.com/name.basics.tsv.gz: 100%|██████████| 214M/214M [00:05<00:00, 39.3MiB/s]
        (11453719, 6)

        We had to download `name.basics.tsv.gz` the first time, but ``get_local_or_remote`` returns immediately the
        second time it is called. Fetching can be forced using ``force=True``.

        >>> path = get_local_or_remote(
        ...     file, remote_root=remote_root, local_root=local_root, show_progress=True
        ... )  # doctest: +SKIP
        >>> pd.read_csv(path, sep="\t").shape  # doctest: +SKIP
        (11453719, 6)

    .. _IMDb dataset:
        https://www.imdb.com/interfaces/
    .. _requests:
        https://requests.readthedocs.io/en/latest/api/#requests
    .. _tqdm:
        https://pypi.org/project/tqdm/

    """
    from ._internal_support._local_or_remote import get_local_or_remote as _impl

    return _impl(
        file=_paths.any_path_to_str(file),
        local_root=_paths.any_path_to_str(local_root),
        remote_root=_paths.any_path_to_str(remote_root),
        force=force,
        postprocessor=postprocessor,
        show_progress=show_progress,
    )


def serializable(obj: object) -> bool:
    """Check if `obj` is serializable using Pickle.

    Args:
        obj: Object to test.

    Returns:
        ``True`` if `obj` was pickled without issues.

    """
    import io
    import pickle

    bio = io.BytesIO()
    try:
        pickle.dump(obj, bio)
        return True  # noqa: TRY300
    except Exception:
        return False
