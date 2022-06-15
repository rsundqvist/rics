from typing import Dict, List, Union

from rics.translation.fetching import Fetcher
from rics.translation.fetching._fetch_instruction import FetchInstruction
from rics.translation.offline import PlaceholderOverrides
from rics.translation.offline.types import (
    IdType,
    NameType,
    PlaceholderOverridesDict,
    PlaceholderTranslations,
    SourcePlaceholderTranslations,
    SourceType,
)


class MemoryFetcher(Fetcher[NameType, IdType, SourceType]):
    """Fetch from memory.

    Args:
        data: A dict {source: PlaceholderTranslations} to fetch from.
        placeholder_overrides: Placeholder name overrides. Used to adapt placeholder names in sources to wanted names.
    """

    def __init__(
        self,
        data: Union[SourcePlaceholderTranslations, Dict[SourceType, PlaceholderTranslations.MakeTypes]],
        placeholder_overrides: Union[PlaceholderOverrides, PlaceholderOverridesDict] = None,
    ) -> None:
        super().__init__(placeholder_overrides=placeholder_overrides)
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
