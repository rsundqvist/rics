"""Implementation of a dict that inherits keys from a fallback collection."""

from typing import Any, Dict, Hashable, Iterator, Mapping, TypeVar, Union

from rics.utility.misc import tname

SKT = TypeVar("SKT", bound=Hashable)
KT = TypeVar("KT", bound=Hashable)
VT = TypeVar("VT")

DefaultType = Dict[KT, VT]
SpecificType = Dict[SKT, DefaultType]
MakeDict = Dict[str, Union[DefaultType, SpecificType]]


class InheritedKeysDict(Mapping[SKT, Dict[KT, VT]]):
    """A nested dictionary that returns default-backed child dictionaries.

    The length of a InheritedKeysDict is equal to the number of specific outer keys, and is considered True when cast to
    bool if there are shared and/or specific keys present.

    Args:
        default: Shared (fallback) mappings for all contexts.
        specific: Context-specific translations, backed by default mappings.

    Examples:
        A short demonstration.

        >>> from rics.utility.collections import InheritedKeysDict
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
        specific: SpecificType = None,
        default: DefaultType = None,
    ) -> None:
        self._specific = specific or {}
        self._default = default or {}

    def __getitem__(self, context: SKT) -> DefaultType:
        if not self:
            raise KeyError(context)

        specific = self._specific.get(context, {})
        return {**self._default, **specific}

    def __repr__(self) -> str:
        default = self._default
        specific = self._specific
        return f"{tname(self)}({default=}, {specific=})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, InheritedKeysDict):
            return False

        return self._default == other._default and self._specific == other._specific  # pragma: no cover

    def __bool__(self) -> bool:
        return bool(self._default or self._specific)

    def __len__(self) -> int:
        return len(self._specific)

    def __iter__(self) -> Iterator[SKT]:
        yield from self._specific

    def copy(self) -> "InheritedKeysDict":
        """Make a copy of this InheritedKeysDict."""
        return InheritedKeysDict(specific=self._specific.copy(), default=self._default.copy())

    @classmethod
    def make(cls, arg: Union["InheritedKeysDict", MakeDict]) -> "InheritedKeysDict":
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
            raise ValueError(f"Invalid {tname(cls)}. Unknown keys: {list(arg)}")

        return InheritedKeysDict(default=default, specific=specific)
