from typing import Dict, List, Union

from rics.mapping import Mapper
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
        mapper: A :class:`~rics.mapping.Mapper` instance used to adapt placeholder names in sources to wanted names, ie
            the names of the placeholders that are in the translation :class:`~rics.offline.Format` being used.
    """

    def __init__(
        self,
        data: Union[SourcePlaceholderTranslations, Dict[SourceType, PlaceholderTranslations.MakeTypes]],
        mapper: Mapper = None,
    ) -> None:
        super().__init__(mapper=mapper)
        self._sources = list(data)
        self._data: SourcePlaceholderTranslations = {
            source: PlaceholderTranslations.make(source, pht) for source, pht in data.items()
        }

    @property
    def sources(self) -> List[SourceType]:
        """Get keys in `data` as a list."""
        return self._sources

    @property
    def placeholders(self) -> Dict[SourceType, List[str]]:
        """Placeholders for sources managed by the fetcher.

        Note that placeholders (and sources) are returned as they appear as they are known to the fetcher, without
        remapping to desired names. As an example, for sources ``cities`` and ``languages``, this property may return::

           placeholders = {
               "cities": ["city_id", "city_name", "location_id"],
               "languages": ["id", "name"],
           }

        Returns:
            A dict ``{source: placeholders_for_source}``.
        """
        return {source: list(pht.placeholders) for source, pht in self._data.items()}

    def fetch_translations(self, instr: FetchInstruction) -> PlaceholderTranslations:
        """Fetch columns from memory."""
        return self._data[instr.source]
