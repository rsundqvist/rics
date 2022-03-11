from dataclasses import dataclass
from typing import Generic, Iterable, Optional

from rics.translation.offline.types import IdType, SourceType


@dataclass(frozen=True)
class IdsToFetch(Generic[SourceType, IdType]):
    """A source and the IDs to fetch from it.

    Attributes:
        source: Where to fetch from.
        ids: Unique IDs to fetch translations for. None=fetch as much as possible.
    """

    source: SourceType
    ids: Optional[Iterable[IdType]]
