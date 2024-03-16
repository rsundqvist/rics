"""Dict utility functions."""

import typing as _t
from warnings import warn as _warn

from ..action_level import ActionLevel as _ActionLevel
from ..misc import get_by_full_name as _get_by_full_name
from ..misc import tname as _tname

KT = _t.TypeVar("KT", bound=_t.Hashable)
"""Key type."""
VT = _t.TypeVar("VT")
"""Value type."""
HVT = _t.TypeVar("HVT", bound=_t.Hashable)
"""Hashable value type."""
OKT = _t.TypeVar("OKT", bound=_t.Hashable)
"""Outer key type."""


def compute_if_absent(d: dict[KT, VT], key: KT, func: _t.Callable[[KT], VT] | None = None) -> VT:
    """Compute and store `key` using `func` if `key` is not in the dict.

    Args:
        d: A dict.
        key: The key to get.
        func: A function to call for missing keys. Perform regular ``__getitem__`` call if ``None``.

    Returns:
        The value of `k` in `d`.

    """
    if not (func is None or key in d):
        d[key] = func(key)

    return d[key]


def reverse_dict(d: _t.Mapping[KT, HVT], duplicate_key_action: _ActionLevel.ParseType = "raise") -> dict[HVT, KT]:
    """Swap keys and values.

    Args:
        d: A dict to reverse.
        duplicate_key_action: Action to take if the return dict has key collisions in the reversed dict, i.e. there are
            duplicate values in `d`. Set to `ignore` to allow.

    Returns:
        A reversed copy of `d`.

    Examples:
        Reversing a dict with two elements.

        >>> reverse_dict({"A": 0, "B": 1})
        {0: 'A', 1: 'B'}

    Raises:
        ValueError: If there are duplicate values in `d` and ``duplicate_key_action='raise'``.

    """
    retval = {value: key for key, value in d.items()}

    action_level = _ActionLevel.verify(duplicate_key_action)
    if action_level is not _ActionLevel.IGNORE and len(d) != len(retval):
        msg = (
            f"Duplicate values in {d}; cannot reverse. Original dict has size {len(d)} != {len(retval)}."
            f"\nHint: Set duplicate_key_action='ignore' to allow."
        )
        if action_level is _ActionLevel.WARN:
            _warn(msg, stacklevel=2)
        else:
            raise ValueError(msg)  # pragma: no cover

    return retval


def flatten_dict(
    d: dict[KT, _t.Any],
    join_string: str = ".",
    filter_predicate: _t.Callable[[KT, _t.Any], bool] = lambda *_: True,
    string_fn: _t.Callable[[KT], str] | str | None = str,
) -> dict[str, _t.Any]:
    """Flatten a nested dictionary.

    This process is partially (or fully; depends on `d` and arguments) reversible, see :func:`unflatten_dict`.

    Args:
        d: A dict to flatten. Keys must be strings.
        join_string: Joiner for nested keys.
        filter_predicate: A callable ``(key, value) -> should_keep``. Default always returns ``True``.
        string_fn: A callable which takes a non-string key value and converts into to a string. If ``None``, a type
            error will be raised for non-string keys. Default is :py:class:`str(key) <str>`. Pass a string to resolve
            using :func:`.get_by_full_name`.

    Returns:
        A flattened version of `d`.

    Examples:
        Flattening a shallow nested dict.

        >>> flatten_dict({"foo": 0, "bar": {"foo": 1, "bar": 2}})
        {'foo': 0, 'bar.foo': 1, 'bar.bar': 2}

    """
    if string_fn is None:

        def no_string_fn(key: _t.Hashable) -> str:
            raise TypeError(f"Cannot convert {key=} with string_fn=None.")

        string_fn = no_string_fn
    elif isinstance(string_fn, str):
        string_fn = _t.cast(_t.Callable[[KT], str], _get_by_full_name(string_fn))

    retval: dict[str, _t.Any] = {}
    _flatten_inner(d, retval, [], join_string, filter_predicate, string_fn)
    return retval


def _flatten_inner(
    d: dict[KT, _t.Any],
    flattened: dict[str, _t.Any],
    parents: list[str],
    join_string: str,
    filter_predicate: _t.Callable[[KT, _t.Any], bool],
    string_fn: _t.Callable[[KT], str],
) -> None:
    for key, value in d.items():
        if not filter_predicate(key, value):
            continue

        str_key = key if isinstance(key, str) else string_fn(key)
        key_hierarchy = [*parents, str_key]
        if isinstance(value, dict):
            _flatten_inner(
                value,
                flattened,
                key_hierarchy,
                join_string,
                filter_predicate,
                string_fn,
            )
        else:
            flat_key = join_string.join(key_hierarchy)
            flattened[flat_key] = value


def unflatten_dict(
    d: dict[str | tuple[str, ...], _t.Any],
    join_string: str = ".",
) -> dict[str, dict[str, _t.Any] | _t.Any]:
    """Unflatten a flat dictionary.

    This process is reversible, see :func:`flatten_dict`.

    Args:
        d: A flat dict to unflatten. Keys must be ``str`` or ``tuple``.
        join_string: Joiner for flattened keys. Ignored if `d` has ``tuple``-keys.

    Returns:
        A nested version of `d`.

    Examples:
        Unflatten a flat dict.

        >>> unflatten_dict({"foo": 0, "bar.foo": 1, "bar.bar": 2})
        {'foo': 0, 'bar': {'foo': 1, 'bar': 2}}

        Tuple keys are also supported, including mixed key types.

        >>> unflatten_dict({"foo": 0, ("bar", "foo"): 1, "bar.bar": 2})
        {'foo': 0, 'bar': {'foo': 1, 'bar': 2}}

    """
    ret: dict[str, dict[str, _t.Any] | _t.Any] = {}
    for key, value in d.items():
        parts: _t.Sequence[str]
        if isinstance(key, str):
            parts = key.split(join_string)
        else:
            parts = key
        final = len(parts) - 1
        current = ret
        for i, p in enumerate(parts):
            if i == final:
                current[p] = value
            else:
                if p not in current:
                    current[p] = {}
                current = current[p]
    return ret


class InheritedKeysDict(_t.Mapping[OKT, dict[KT, VT]]):
    """A nested dictionary that returns default-backed child dictionaries.

    The length of an ``InheritedKeysDict`` is equal to the number of specific outer keys, and is considered ``True``
    when cast to bool if there are shared and/or specific keys present.

    Args:
        default: Shared (fallback) mappings for all contexts.
        specific: Context-specific mappings, backed by the default fallback mappings.

    Examples:
        A short demonstration.

        >>> shared = {0: "fallback-for-0", 1: "fallback-for-1"}
        >>> specific = {
        ...     "ctx0": {0: "c0-v0"},
        ...     "ctx1": {0: "c1-v0", 1: "c1-v1", 2: "c1-v2"},
        ... }
        >>> ikd = InheritedKeysDict(default=shared, specific=specific)
        >>> ikd
        InheritedKeysDict(default={0: 'fallback-for-0', 1: 'fallback-for-1'}, specific={'ctx0': {0: 'c0-v0'},
        'ctx1': {0: 'c1-v0', 1: 'c1-v1', 2: 'c1-v2'}})

        The value of key `0` is inherited for `'ctx0'`. The `'ctx1'`-context
        defines all shared keys, as well as a unique key.

        >>> ikd["ctx0"]
        {0: 'c0-v0', 1: 'fallback-for-1'}
        >>> ikd["ctx1"]
        {0: 'c1-v0', 1: 'c1-v1', 2: 'c1-v2'}

        The ``InheritedKeysDict.__contains__``-method is ``True`` for all keys.
        Unknown keys simply return the default values. This will be an empty
        if no specific keys are specified.

        >>> "unseen-key" in ikd
        True
        >>> ikd["unseen-key"]
        {0: 'fallback-for-0', 1: 'fallback-for-1'}

        The length of `ikd` is equal to the number of specific contexts (two in this case).
    """

    def __init__(
        self,
        specific: dict[OKT, dict[KT, VT]] | None = None,
        default: dict[KT, VT] | None = None,
    ) -> None:
        self._specific = specific or {}
        self._default = default or {}

    def __getitem__(self, context: OKT) -> dict[KT, VT]:
        if not self:
            raise KeyError(context)

        specific = self._specific.get(context, {})
        return {**self._default, **specific}

    def __repr__(self) -> str:
        default = self._default
        specific = self._specific
        return f"{_tname(self)}({default=}, {specific=})"

    def __eq__(self, other: _t.Any) -> bool:
        if not isinstance(other, InheritedKeysDict):
            return False

        return self._default == other._default and self._specific == other._specific

    def __bool__(self) -> bool:
        return bool(self._default or self._specific)

    def __len__(self) -> int:
        return len(self._specific)

    def __iter__(self) -> _t.Iterator[OKT]:
        yield from self._specific

    def copy(self) -> "InheritedKeysDict[OKT, KT, VT]":
        """Make a copy of this ``InheritedKeysDict``."""
        return InheritedKeysDict(specific=self._specific.copy(), default=self._default.copy())

    @classmethod
    def make(cls, arg: "MakeType[OKT, KT, VT]") -> "InheritedKeysDict[OKT, KT, VT]":
        """Create instance from a mapping.

        The given argument must be on the format::

            {
                "default": {key: value},
                "specific": {
                    ctx0: {key: value},
                    ctx1: {key: value},
                    ...
                    ctxN: {key: value},
                }
            }

        No other top-level keys are accepted, but neither `default` nor `context-specific` are required.

        Args:
            arg: Input to make an instance from.

        Returns:
            A new instance.

        Raises:
            ValueError: If there are any keys other than 'default' and 'context-specific' present in `mapping`.

        """
        if isinstance(arg, InheritedKeysDict):  # pragma: no cover
            return arg

        default: dict[KT, VT] | None = arg.pop("default", None)
        specific: dict[OKT, dict[KT, VT]] | None = arg.pop("specific", None)

        if arg:  # pragma: no cover
            raise ValueError(f"Unknown keys: {list(arg)}")

        return InheritedKeysDict(default=default, specific=specific)


class _MakeDict(_t.TypedDict, _t.Generic[OKT, KT, VT], total=False):
    default: dict[KT, VT]
    specific: dict[OKT, dict[KT, VT]]


MakeType = InheritedKeysDict[OKT, KT, VT] | _MakeDict[OKT, KT, VT]
"""Valid input types for making the :meth:`InheritedKeysDict.make` function."""
