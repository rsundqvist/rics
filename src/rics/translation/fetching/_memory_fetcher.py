from typing import Any, List

from rics.translation.fetching import Fetcher
from rics.translation.fetching._fetch_instruction import FetchInstruction
from rics.translation.offline.types import IdType, NameType, PlaceholdersDict, SourcePlaceholdersDict, SourceType


class MemoryFetcher(Fetcher[NameType, IdType, SourceType]):
    """Fetch from memory.

    Args:
        data: A dict ``{source: {placeholder: [values..]}}`` to fetch from.
        **kwargs: Forwarded to the base fetcher.
    """

    def __init__(self, data: SourcePlaceholdersDict, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._sources = list(data)
        self._data = data

    @property
    def sources(self) -> List[SourceType]:
        """Get keys in `data` as a list."""
        return self._sources

    def fetch_placeholders(self, instr: FetchInstruction) -> PlaceholdersDict:
        """Fetch columns from memory."""
        return self._data[instr.source]
