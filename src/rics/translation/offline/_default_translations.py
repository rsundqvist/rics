import logging
from typing import Any, Dict, Iterator, Mapping, Optional

from rics.translation.offline.types import DefaultTranslationsDict, SourceType
from rics.utility.misc import tname

LOGGER = logging.getLogger(__package__).getChild("DefaultTranslations")


class DefaultTranslations(Mapping[SourceType, Dict[str, Any]]):
    """Remapping from non-compliant to compliant placeholder names.

    Format is ``<what-it-is> => <what-it-should-be>``.

    Args:
        shared: Mappings shared by all sources.
        source_specific: Source-specific mappings, backed by shared mappings.
    """

    def __init__(
        self,
        shared: Dict[str, Any] = None,
        source_specific: Dict[SourceType, Dict[str, Any]] = None,
    ) -> None:
        self._shared = shared or {}
        self._specific: Dict[SourceType, Dict[str, Any]] = source_specific or {}

    def __getitem__(self, source: SourceType) -> Dict[str, Any]:
        specific = self._specific.get(source) or {}
        return {**self._shared, **specific}

    def __setitem__(self, source: SourceType, value: Dict[str, Any]) -> None:
        self._specific[source] = value

    def __len__(self) -> int:
        return len(self._specific)

    def __iter__(self) -> Iterator[SourceType]:
        yield from self._specific

    def __repr__(self) -> str:
        shared = self._shared
        source_specific = self._specific
        return f"{tname(self)}({shared=}, {source_specific=})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, DefaultTranslations):
            return False

        return self._shared == other._shared and self._specific == other._specific

    @classmethod
    def from_dict(cls, mapping: DefaultTranslationsDict) -> "DefaultTranslations":
        """Create instance from a mapping.

        The given argument must follow the format specified below::

            {
                "shared": {placeholder: value},
                "source-specific": {
                    source0: {placeholder: value},
                    source1: {placeholder: value},
                    ...
                    sourceN: {placeholder: value},
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

        return DefaultTranslations(shared, source_specific)
