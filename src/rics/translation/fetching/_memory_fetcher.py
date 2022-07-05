from typing import TYPE_CHECKING, Dict, List, Union

if TYPE_CHECKING:
    from rics.translation.offline import Format  # noqa: F401

from rics.mapping import Mapper
from rics.translation.fetching import AbstractFetcher
from rics.translation.fetching.types import FetchInstruction
from rics.translation.offline.types import PlaceholderTranslations, SourcePlaceholderTranslations
from rics.translation.types import SourceType


class MemoryFetcher(AbstractFetcher):
    """Fetch from memory.

    Args:
        data: A dict ``{source: PlaceholderTranslations}`` to fetch from.
        mapper: A :class:`.Mapper` instance used to adapt placeholder names in sources to wanted names, ie
            the names of the placeholders that are in the translation :class:`.Format` being used.
    """

    def __init__(
        self,
        data: Union[SourcePlaceholderTranslations, Dict[SourceType, PlaceholderTranslations.MakeTypes]],
        mapper: Mapper = None,
    ) -> None:
        super().__init__(mapper=mapper)
        self._data: SourcePlaceholderTranslations = {
            source: PlaceholderTranslations.make(source, pht) for source, pht in data.items()
        }

    @property
    def sources(self) -> List[SourceType]:
        return list(self._data)

    @property
    def placeholders(self) -> Dict[SourceType, List[str]]:
        return {source: list(pht.placeholders) for source, pht in self._data.items()}

    def fetch_translations(self, instr: FetchInstruction) -> PlaceholderTranslations:
        return self._data[instr.source]
