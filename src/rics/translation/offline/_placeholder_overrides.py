import logging
from typing import Any, Dict, Generic, Hashable, Optional, TypeVar

from rics.translation.offline.types import PlaceholderOverridesDict, SourceType
from rics.utility.misc import tname

T = TypeVar("T", bound=Hashable)
LOGGER = logging.getLogger(__package__).getChild("PlaceholderOverrides")


class PlaceholderOverrides(Generic[SourceType]):
    """Remapping from non-compliant to compliant placeholder names.

    Format is ``<what-it-is> => <what-it-should-be>``.

    Args:
        shared: Mappings shared by all sources.
        source_specific: Source-specific mappings, backed by shared mappings.
        reversed_direction: Indicates reversal, ie format has become ``<what-it-is> <= <what-it-should-be>``.
    """

    def __init__(
        self,
        shared: Dict[str, str] = None,
        source_specific: Dict[SourceType, Dict[str, str]] = None,
        reversed_direction: bool = False,
    ) -> None:
        self._shared = shared or {}
        self._specific: Dict[SourceType, Dict[str, str]] = source_specific or {}
        self._rev = reversed_direction

    @classmethod
    def get_mapped_value(cls, key: T, mapping: Dict[T, T]) -> T:
        """Get the value mapped to `key`.

        If `key` is it not present in `mapping`, `key` is returned to the caller.

        Args:
            key: A value to convert.
            mapping: The mapping to use.

        Returns:
            The original key or ``mapping[value]``.
        """
        return mapping.get(key) or key

    def __getitem__(self, source: SourceType) -> Dict[str, str]:
        specific = self._specific.get(source)
        ans = self._shared if not specific else {**self._shared, **({} if specific is None else specific)}
        if LOGGER.isEnabledFor(logging.DEBUG) and ans:
            specific_overrides = "" if not specific else f"; specific for this source: {specific}"
            LOGGER.debug(f"{self._reversed_str}Overrides for {source=}: {ans}{specific_overrides}.")
        return ans

    def reverse(self) -> "PlaceholderOverrides":
        """Return a reversed copy of self, swapping `from_placeholder` <-> `to_placeholder`."""
        return PlaceholderOverrides(
            shared=self._reverse_mappings(self._shared),
            source_specific={source: self._reverse_mappings(mappings) for source, mappings in self._specific.items()},
            reversed_direction=not self._rev,
        )

    def __bool__(self) -> bool:
        return bool(self._shared or self._specific)

    def __repr__(self) -> str:
        shared = self._shared
        return f"{tname(self)}({self._reversed_str}{shared=} + {len(self._specific)} source-specific)"

    @property
    def _reversed_str(self) -> str:
        return "[REVERSED] " if self._rev else ""  # pragma: no cover

    @classmethod
    def from_dict(cls, mapping: PlaceholderOverridesDict) -> "PlaceholderOverrides":
        """Create instance from a mapping.

        The given argument must follow the format specified below::

            {
                "shared": {from_placeholder: to_placeholder},
                "source-specific": {
                    source0: {from_placeholder: to_placeholder},
                    source1: {from_placeholder: to_placeholder},
                    ...
                    sourceN: {from_placeholder: to_placeholder},
                }
            }

        No other top-level keys are accepted, but neither `shared` nor `source-specific` are required.

        Args:
            mapping: A remapping dict.

        Returns:
            A new instance.

        Raises:
            ValueError: If there are any keys other than 'shared' and 'source-specific' present in `mapping`.
        """
        shared: Optional[Dict[str, Any]] = mapping.pop("shared", None)
        source_specific: Optional[Dict[str, Any]] = mapping.pop("source-specific", None)

        if mapping:
            raise ValueError(f"Invalid remapping dict. Unknown keys: {list(mapping)}")

        return PlaceholderOverrides(shared, source_specific)

    @staticmethod
    def _reverse_mappings(mappings: Dict[str, str]) -> Dict[str, str]:
        return {to_ph: from_ph for from_ph, to_ph in mappings.items()}
