"""Types related to translation fetching."""

from dataclasses import dataclass
from typing import Generic, Iterable, Optional, Set

from rics.translation.offline.types import PlaceholdersTuple
from rics.translation.types import IdType, SourceType


@dataclass(frozen=True)
class IdsToFetch(Generic[SourceType, IdType]):
    """A source and the IDs to fetch from it."""

    source: SourceType
    """Where to fetch from."""
    ids: Optional[Iterable[IdType]]
    """Unique IDs to fetch translations for. None=fetch as much as possible."""


@dataclass(frozen=True)
class FetchInstruction(IdsToFetch):
    """Instructions passed from an abstract fetcher to an implementation."""

    placeholders: PlaceholdersTuple
    """All desired placeholders in preferred order."""
    required: Set[str]
    """Placeholders that must be included in the response."""
    all_placeholders: bool
    """Flag indicated whether to retrieve as many placeholders as possible."""
