"""Dict utility functions."""
import warnings
from typing import Any, Callable, Dict, Hashable, Iterator, List, Mapping, Optional, TypedDict, TypeVar, Union

from ..action_level import ActionLevel
from ..misc import tname as _tname

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

        >>> from rics.collections.dicts import reverse_dict
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

        >>> from rics.collections.dicts import flatten_dict
        >>> flatten_dict({"foo": 0, "bar": {"foo": 1, "bar": 2}})
        {'foo': 0, 'bar.foo': 1, 'bar.bar': 2}
    """
    ans: Dict[str, Any] = {}
    _flatten_inner(d, ans, [], join_string, filter_predicate)
    return ans


def _flatten_inner(
    d: Dict[str, Any],
    flattened: Dict[str, Any],
    parents: List[str],
    join_string: str,
    filter_predicate: Optional[Callable[[str, Any], bool]],
) -> None:
    for key, value in d.items():
        if filter_predicate is not None and not filter_predicate(key, value):
            continue

        key_hierarchy = parents + [key]
        if isinstance(value, dict):
            _flatten_inner(value, flattened, key_hierarchy, join_string, filter_predicate)
        else:
            flat_key = join_string.join(key_hierarchy)
            flattened[flat_key] = value


class InheritedKeysDict(Mapping[OKT, Dict[KT, VT]]):
    """A nested dictionary that returns default-backed child dictionaries.

    The length of an ``InheritedKeysDict`` is equal to the number of specific outer keys, and is considered ``True``
    when cast to bool if there are shared and/or specific keys present.

    Args:
        default: Shared (fallback) mappings for all contexts.
        specific: Context-specific mappings, backed by the default fallback mappings.

    Examples:
        A short demonstration.

        >>> from rics.collections.dicts import InheritedKeysDict
        >>> shared = {0: 'fallback-for-0', 1: 'fallback-for-1'}
        >>> specific = {
        ...     'ctx0': {0: 'c0-v0'},
        ...     'ctx1': {0: 'c1-v0', 1: 'c1-v1', 2: 'c1-v2'},
        ... }
        >>> ikd = InheritedKeysDict(default=shared, specific=specific); ikd
        InheritedKeysDict(default={0: 'fallback-for-0', 1: 'fallback-for-1'}, specific={'ctx0': {0: 'c0-v0'},
        'ctx1': {0: 'c1-v0', 1: 'c1-v1', 2: 'c1-v2'}})

        The value of key `0` is inherited for `'ctx0'`. The `'ctx1'`-context
        defines all shared keys, as well as a unique key.

        >>> ikd['ctx0']
        {0: 'c0-v0', 1: 'fallback-for-1'}
        >>> ikd['ctx1']
        {0: 'c1-v0', 1: 'c1-v1', 2: 'c1-v2'}

        The ``InheritedKeysDict.__contains__``-method is ``True`` for all keys.
        Unknown keys simply return the default values. This will be an empty
        if no specific keys are specified.

        >>> 'unseen-key' in ikd
        True
        >>> ikd['unseen-key']
        {0: 'fallback-for-0', 1: 'fallback-for-1'}

        The length of `ikd` is equal to the number of specific contexts (two in this case).
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
            raise KeyError(context)  # pragma: no cover

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

        # TODO: Need 3.11 and MakeDict for these
        default: Optional[Dict[KT, VT]] = arg.pop("default", None)
        specific: Optional[Dict[OKT, Dict[KT, VT]]] = arg.pop("specific", None)

        if arg:  # pragma: no cover
            raise ValueError(f"Invalid {_tname(cls)}. Unknown keys: {list(arg)}")

        return InheritedKeysDict(default=default, specific=specific)


class _MakeDict(
    TypedDict,
    total=False,
    # Generic[OKT, KT, VT] # TODO: Requires 3.11
):
    default: Dict[KT, VT]  # type: ignore[valid-type]
    specific: Dict[OKT, Dict[KT, VT]]  # type: ignore[valid-type]


MakeType = Union[
    InheritedKeysDict[OKT, KT, VT],
    _MakeDict,
    # MakeDict[OKT, KT, VT],
]
"""Valid input types for making the :meth:`InheritedKeysDict.make` function."""
