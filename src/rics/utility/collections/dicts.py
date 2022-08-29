"""Dict utility functions."""
import warnings
from typing import Any, Callable, Dict, Hashable, Iterator, List, Mapping, TypeVar, Union

from rics.utility.action_level import ActionLevel
from rics.utility.misc import tname as _tname

KT = TypeVar("KT", bound=Hashable)
"""Key type."""
VT = TypeVar("VT")
"""Value type."""
HVT = TypeVar("HVT", bound=Hashable)
"""Hashable value type."""
OKT = TypeVar("OKT", bound=Hashable)
"""Outer key type."""


def compute_if_absent(d: Dict[KT, VT], key: KT, func: Callable[[KT], VT] = None) -> VT:
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


def reverse_dict(d: Mapping[KT, HVT], duplicate_key_action: ActionLevel.ParseType = "raise") -> Dict[HVT, KT]:
    """Swap keys and values.

    Args:
        d: A dict to reverse.
        duplicate_key_action: Action to take if the return dict has key collisions in the reversed dict, i.e. there are
            duplicate values in `d`. Set to `ignore` to allow.

    Returns:
        A reversed copy of `d`.

    Examples:
        Reversing a dict with two elements.

        >>> from rics.utility.collections.dicts import reverse_dict
        >>> reverse_dict({"A": 0, "B": 1})
        {0: 'A', 1: 'B'}

    Raises:
        ValueError: If there are duplicate values in `d` and ``duplicate_key_action='raise'``.
    """
    ans = {value: key for key, value in d.items()}
    action_level = ActionLevel.verify(duplicate_key_action)

    if action_level is not ActionLevel.IGNORE and len(d) != len(ans):  # pragma: no cover
        msg = (
            f"Duplicate values in {d}; cannot reverse. Original dict has size {len(d)} != {len(ans)}."
            f"\nHint: Set duplicate_key_action='ignore' to allow."
        )
        if action_level is ActionLevel.WARN:
            warnings.warn(msg)
        elif action_level is ActionLevel.RAISE:
            raise ValueError(msg)

    return ans


def flatten_dict(
    d: Dict[str, Any],
    join_string: str = ".",
    filter_predicate: Callable[[str, Any], bool] = None,
) -> Dict[str, Any]:
    """Flatten a nested dictionary.

    Args:
        d: A dict to flatten. Keys must be strings.
        join_string: Joiner for nested keys.
        filter_predicate: A callable which takes a key and value, returning ``True`` if the entry should be kept.

    Returns:
        A flattened version of `d`.

    Examples:
        Flattening a shallow nested dict.

        >>> from rics.utility.collections.dicts import flatten_dict
        >>> flatten_dict({"foo": 0, "bar": {"foo": 1, "bar": 2}})
        {'foo': 0, 'bar.foo': 1, 'bar.bar': 2}
    """
    return _flatten_inner(d, {}, [], join_string, filter_predicate)


def _flatten_inner(
    arg: Any,
    flattened: Dict[str, Any],
    parents: List[str],
    join_string: str = ".",
    filter_predicate: Callable[[str, Any], bool] = None,
) -> Dict[str, Any]:
    if isinstance(arg, dict):
        for key, value in arg.items():
            if filter_predicate is not None and not filter_predicate(key, value):
                continue
            new_parents = parents + [key]
            flat_key = join_string.join(new_parents)
            inner = _flatten_inner(value, flattened, new_parents, join_string, filter_predicate)
            if not isinstance(inner, dict):
                flattened[flat_key] = inner
        return flattened
    else:
        return arg


class InheritedKeysDict(Mapping[OKT, Dict[KT, VT]]):
    """A nested dictionary that returns default-backed child dictionaries.

    The length of an ``InheritedKeysDict`` is equal to the number of specific outer keys, and is considered ``True``
    when cast to bool if there are shared and/or specific keys present.

    Args:
        default: Shared (fallback) mappings for all contexts.
        specific: Context-specific translations, backed by default mappings.

    Examples:
        A short demonstration.

        >>> from rics.utility.collections.dicts import InheritedKeysDict
        >>> shared = {0: "shared0", 1: "shared1"}
        >>> specific = {
        ... "ctx0": {0: "c0-v0"},
        ... "ctx1": {0: "c1-v0", 1: "c1-v1"},
        ... }
        >>> d = InheritedKeysDict(default=shared, specific=specific)
        >>> d
        InheritedKeysDict(default={0: 'shared0', 1: 'shared1'},
        specific={'ctx0': {0: 'c0-v0'}, 'ctx1': {0: 'c1-v0', 1: 'c1-v1'}})
        >>> d["ctx0"]  # Value of key 0 is inherited
        {0: 'c0-v0', 1: 'shared1'}
        >>> d["ctx1"]  # Both keys are specified, so nothing is inherited
        {0: 'c1-v0', 1: 'c1-v1'}
        >>> "not-in-d" in d  # With defaults, all keys are considered as part of d..
        True
        >>> d["not-in-d"]  # ..but, 'not-in-d' unknowns inherit all keys
        {0: 'shared0', 1: 'shared1'}
        >>> len(d)  # The length of d is equal to the number of specific contexts
        2
    """

    def __init__(
        self,
        specific: Dict[OKT, Dict[KT, VT]] = None,
        default: Dict[KT, VT] = None,
    ) -> None:
        self._specific = specific or {}
        self._default = default or {}

    def __getitem__(self, context: OKT) -> Dict[KT, VT]:
        if not self:
            raise KeyError(context)

        specific = self._specific.get(context, {})
        return {**self._default, **specific}

    def __repr__(self) -> str:
        default = self._default
        specific = self._specific
        return f"{_tname(self)}({default=}, {specific=})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, InheritedKeysDict):
            return False

        return self._default == other._default and self._specific == other._specific  # pragma: no cover

    def __bool__(self) -> bool:
        return bool(self._default or self._specific)

    def __len__(self) -> int:
        return len(self._specific)

    def __iter__(self) -> Iterator[OKT]:
        yield from self._specific

    def copy(self) -> "InheritedKeysDict":
        """Make a copy of this ``InheritedKeysDict``."""
        return InheritedKeysDict(specific=self._specific.copy(), default=self._default.copy())

    @classmethod
    def make(cls, arg: "MakeType") -> "InheritedKeysDict":
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

        default = arg.pop("default", None)
        specific = arg.pop("specific", None)

        if arg:  # pragma: no cover
            raise ValueError(f"Invalid {_tname(cls)}. Unknown keys: {list(arg)}")

        return InheritedKeysDict(default=default, specific=specific)


MakeType = Union[Dict[str, Union[Dict[KT, VT], Dict[OKT, Dict[KT, VT]]]], InheritedKeysDict[OKT, KT, VT]]
"""Valid input types for making the :meth:`InheritedKeysDict.make` function."""
