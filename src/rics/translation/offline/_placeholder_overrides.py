import logging
from typing import Any, Dict, Generic, Optional

from rics.translation.offline.types import PlaceholderOverridesDict, SourceType
from rics.utility.misc import tname

LOGGER = logging.getLogger(__package__).getChild("PlaceholderOverrides")


class PlaceholderOverrides(Generic[SourceType]):
    """Remapping from non-compliant to compliant placeholder names.

    Format is ``<what-it-is> => <what-it-should-be>``.

    Args:
        shared: Mappings shared by all sources.
        source_specific: Source-specific mappings, backed by shared mappings.
    """

    def __init__(
        self,
        shared: Dict[str, str] = None,
        source_specific: Dict[SourceType, Dict[str, str]] = None,
    ) -> None:
        self._shared = shared or {}
        self._specific: Dict[SourceType, Dict[str, str]] = source_specific or {}
        self._is_reversed = False
        self._reverse: Optional[PlaceholderOverrides] = None

    def __getitem__(self, source: SourceType) -> Dict[str, str]:
        specific = self._specific.get(source)
        return self._shared if not specific else {**self._shared, **({} if specific is None else specific)}

    def info_string(self, source: SourceType) -> str:  # pragma: no cover
        """Get an override info string for `source`."""
        specific = self._specific.get(source)
        ans = self[source]
        if specific:
            specific_overrides = "; unique to source" if (ans == specific) else f"; specific to source: {specific}"
        else:
            specific_overrides = ""
        return f"Overrides for {source=}: {ans}{specific_overrides}."

    def reverse(self) -> "PlaceholderOverrides":
        """Return a reversed copy of self, swapping `from_placeholder` <-> `to_placeholder`."""
        if self._reverse is None:
            self._reverse = self._init_reverse()

        return self._reverse

    def _init_reverse(self) -> "PlaceholderOverrides":
        reversed_overrides = PlaceholderOverrides(
            shared=self._reverse_mappings(self._shared),
            source_specific={source: self._reverse_mappings(mappings) for source, mappings in self._specific.items()},
        )
        reversed_overrides._is_reversed = True
        reversed_overrides._reverse = self
        return reversed_overrides

    def __bool__(self) -> bool:
        return bool(self._shared or self._specific)

    def __repr__(self) -> str:
        shared = self._shared
        reversed_str = "[REVERSED] " if self._is_reversed else ""
        return f"{tname(self)}({reversed_str}{shared=} + {len(self._specific)} source-specific)"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, PlaceholderOverrides):
            return False

        return self._shared == other._shared and self._specific == other._specific  # pragma: no cover

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
