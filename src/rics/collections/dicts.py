"""Dict utility functions."""

import typing as _t
from functools import cached_property as _cached_property
from warnings import warn as _warn

from ..action_level import ActionLevel as _ActionLevel
from ..misc import get_by_full_name as _get_by_full_name
from ..misc import tname as _tname

KT = _t.TypeVar("KT", bound=_t.Hashable)
"""Key type."""
VT = _t.TypeVar("VT")
"""Value type."""
VT_co = _t.TypeVar("VT_co", covariant=True)
"""Covariant type."""
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


def format_changed_keys(
    mapping: _t.Mapping[KT, VT_co],
    *,
    baseline: _t.Mapping[KT, VT_co],
    added: bool | _t.Literal["keys"] = True,
    updated: bool | _t.Literal["keys"] = True,
    removed: bool | _t.Literal["keys"] = "keys",
) -> str:
    """Format difference from a `baseline` mapping.

    Pass ``'keys'`` instead of ``True`` / ``False`` to show affected keys without values.

    Args:
        mapping: The current mapping.
        baseline: A baseline mapping.
        added: Determines how and if to print :attr:`~DictComparer.added` keys.
        updated: Determines how and if to print :attr:`~DictComparer.updated` keys.
        removed: Determines how and if to print :attr:`~DictComparer.removed` keys.

    Returns:
        Stylized difference between a `mapping` and the `baseline`.

    Examples:
        >>> mapping = {0: None, 1: 1, -1: None}
        >>> b = {0: 0, 1: 1, 2: 2}  # baseline

        Default behavior.

        >>> format_changed_keys(mapping, baseline=b)
        'added(1): {-1: None}, updated(1): {0: None}, removed(1): {2}'

        Showing added keys without values.

        >>> format_changed_keys(mapping, baseline=b, added="keys")
        'added(1): {-1}, updated(1): {0: None}, removed(1): {2}'

        Removed keys are printed without values by default. Passing ``True`` prints the values.

        >>> format_changed_keys(mapping, baseline=b, removed=True)
        'added(1): {-1: None}, updated(1): {0: None}, removed(1): {2: 2}'

        To hide a change type entirely, pass ``False`` instead.

        >>> format_changed_keys(mapping, baseline=b, updated=False)
        'added(1): {-1: None}, removed(1): {2}'

    Notes:
        This is a convenience function that warps :func:`DictComparer.to_string`.
    """
    return DictComparer(mapping, baseline=baseline).to_string(added=added, updated=updated, removed=removed)


_ChangesByType = dict[str, set[KT] | dict[KT, VT_co]]


class DictComparer(_t.Generic[KT, VT_co]):
    """Utility class for comparing mapping types.

    Args:
        mapping: The current mapping.
        baseline: A baseline mapping.
        preference: Determines values in :attr:`updated`. Set to `'old'` to prefer `baseline` values.

    Notes:
        * Properties are cached.
        * ``DictComparer.__str__`` is :meth:`DictComparer.to_string`.
    """

    Preference = _t.Literal["old", "new"]
    """Value preference for :attr:`updated` keys."""

    def __init__(
        self,
        mapping: _t.Mapping[KT, VT_co],
        *,
        baseline: _t.Mapping[KT, VT_co],
        preference: Preference = "new",
    ) -> None:
        from rics.types import verify_literal

        self._baseline = baseline
        self._mapping = {} if mapping is None else mapping

        verify_literal(preference, DictComparer.Preference, name="preference")
        self._prefer_new = preference == "new"

    def to_string(
        self,
        *,
        added: bool | _t.Literal["keys"] = True,
        updated: bool | _t.Literal["keys"] = True,
        removed: bool | _t.Literal["keys"] = "keys",
        formatter: _t.Callable[[_ChangesByType[KT, VT_co]], str] | None = None,
    ) -> str:
        """Format :attr:`changed` keys.

        Pass ``'keys'`` instead of ``True`` / ``False`` to show affected keys without values.

        Args:
            added: Determines how and if to print :attr:`added` keys.
            updated: Determines how and if to print :attr:`updated` keys.
            removed: Determines how and if to print :attr:`removed` keys.
            formatter: A callable ``({change_type: {key: value} | {key, ...}) -> str``, where
                ``change_type = 'added'|'updated'|'removed'``. Use :meth:`default_formatter` if ``None``.

        Returns:
            Pretty-printed changes.
        """
        if not (added or updated or removed):
            msg = "At least one of {'added', 'updated', 'removed'} must be set"
            raise TypeError(msg)

        changes_by_type: _ChangesByType[KT, VT_co] = {}
        if added and (added_ := self.added):
            changes_by_type["added"] = added_ if added is True else set(added_)
        if updated and (updated_ := self.updated):
            changes_by_type["updated"] = updated_ if updated is True else set(updated_)
        if removed and (removed_ := self.removed):
            changes_by_type["removed"] = removed_ if removed is True else set(removed_)

        if formatter is None:
            formatter = self.default_formatter
        return formatter(changes_by_type)

    @property
    def baseline(self) -> _t.Mapping[KT, VT_co]:
        """Get the original `baseline` mapping."""
        return self._baseline

    @property
    def mapping(self) -> _t.Mapping[KT, VT_co]:
        """Get the original `mapping`."""
        return self._mapping

    @property
    def preference(self) -> Preference:
        """Value preference for :attr:`updated` key."""
        return "new" if self._prefer_new else "old"

    __str__ = to_string

    def __repr__(self) -> str:
        mapping = self.mapping
        baseline = self.baseline
        preference = self.preference
        return f"{type(self).__name__}({mapping=}, {baseline=}, {preference=})"

    @property
    def total(self) -> int:
        """Total number of :attr:`changed` keys."""
        return len(self.changed)

    @_cached_property
    def changed(self) -> dict[KT, VT_co]:
        """Get a dict containing all :attr:`added`, :attr:`changed` or :attr:`removed` keys."""
        return {**self.added, **self.updated, **self.removed}

    @_cached_property
    def added(self) -> dict[KT, VT_co]:
        """Get a dict containing new keys."""
        return {k: v for k, v in self._mapping.items() if k not in self._baseline}

    @_cached_property
    def removed(self) -> dict[KT, VT_co]:
        """Get a dict containing removed keys."""
        return {k: v for k, v in self._baseline.items() if k not in self._mapping}

    @_cached_property
    def updated(self) -> dict[KT, VT_co]:
        """Get a dict containing updated values (see :attr:`preference`) for :attr:`baseline` keys."""
        baseline = self._baseline
        mapping = self._mapping

        updated = {}
        for key in set(baseline).intersection(mapping):
            old = baseline[key]
            new = mapping[key]

            if old != new:
                # if self._recursive and isinstance(new, _t.Mapping) and isinstance(old, _t.Mapping):
                #    cls = type(self)
                #    updated_child = cls(new, baseline=old, preference=self.preference, recursive=True).updated
                #    updated[key] = updated_child
                # else:
                updated[key] = new if self._prefer_new else old

        return updated

    @classmethod
    def default_formatter(cls, changes_by_type: _ChangesByType[_t.Any, _t.Any]) -> str:
        """Default formatting implementation."""
        return ", ".join(
            f"{change_type}({len(changes):_d}): {changes!r}"  # count and type
            for change_type, changes in changes_by_type.items()
        )
