from typing import Any, Dict, List, Union

from rics.translation.fetching import Fetcher
from rics.translation.fetching._fetch_instruction import FetchInstruction
from rics.translation.offline.types import (
    IdType,
    NameType,
    PlaceholderTranslations,
    SourcePlaceholderTranslations,
    SourceType,
)


class MemoryFetcher(Fetcher[NameType, IdType, SourceType]):
    """Fetch from memory.

    Args:
        data: A dict {source: PlaceholderTranslations} to fetch from.
        **kwargs: Forwarded to the base fetcher.
    """

    def __init__(
        self,
        data: Union[SourcePlaceholderTranslations, Dict[SourceType, PlaceholderTranslations.MakeTypes]],
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._sources = list(data)
        self._data: SourcePlaceholderTranslations = {
            source: PlaceholderTranslations.make(source, pht) for source, pht in data.items()
        }

    @property
    def sources(self) -> List[SourceType]:
        """Get keys in `data` as a list."""
        return self._sources

    def fetch_placeholders(self, instr: FetchInstruction) -> PlaceholderTranslations:
        """Fetch columns from memory."""
        ans = self._data[instr.source]
        Fetcher.verify_placeholders(instr, ans.placeholders)
        return ans
