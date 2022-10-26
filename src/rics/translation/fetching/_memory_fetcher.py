from typing import Any, Dict, List, Mapping, Sequence, Union

import pandas as pd

from rics.translation.fetching import AbstractFetcher
from rics.translation.fetching.types import FetchInstruction
from rics.translation.offline.types import PlaceholderTranslations, SourcePlaceholderTranslations
from rics.translation.types import IdType, SourceType


class MemoryFetcher(AbstractFetcher[SourceType, IdType]):
    """Fetch from memory.

    Args:
        data: A dict ``{source: PlaceholderTranslations}`` to fetch from.
    """

    def __init__(
        self,
        data: Union[
            SourcePlaceholderTranslations[SourceType],
            Dict[SourceType, PlaceholderTranslations[SourceType]],
            Dict[SourceType, pd.DataFrame],
            Mapping[SourceType, Mapping[str, Sequence[Any]]],
        ] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._data: SourcePlaceholderTranslations[SourceType] = (
            {} if not data else {source: PlaceholderTranslations.make(source, pht) for source, pht in data.items()}
        )

    @property
    def sources(self) -> List[SourceType]:
        return list(self._data)

    @property
    def placeholders(self) -> Dict[SourceType, List[str]]:
        return {source: list(pht.placeholders) for source, pht in self._data.items()}

    def fetch_translations(self, instr: FetchInstruction[SourceType, IdType]) -> PlaceholderTranslations[SourceType]:
        return self._data[instr.source]
