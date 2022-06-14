from typing import Any, Dict, List, Optional, Sequence, TypeVar

import pandas as pd

from rics.translation.dio._data_structure_io import DataStructureIO
from rics.translation.offline import TranslationMap
from rics.translation.offline.types import IdType, NameType

T = TypeVar("T", pd.DataFrame, pd.Series)


class PandasIO(DataStructureIO):
    """Implementation for Pandas data types."""

    @staticmethod
    def handles_type(arg: Any) -> bool:
        """Return True if the implementation handles data for the type of `arg`."""
        return isinstance(arg, (pd.DataFrame, pd.Series))

    @staticmethod
    def extract(translatable: T, names: List[NameType]) -> Dict[NameType, Sequence[IdType]]:
        """Extract IDs from a pandas object `translatable`."""
        if isinstance(translatable, pd.DataFrame):
            return translatable[names]
        else:
            return translatable

    @staticmethod
    def insert(translatable: T, names: List[NameType], tmap: TranslationMap, copy: bool) -> Optional[T]:
        """Insert translations into a Pandas type."""
        translatable = translatable.copy() if copy else translatable

        if isinstance(translatable, pd.DataFrame):
            for name in names:
                translatable[name] = translatable[name].map(tmap[name].get)
        else:
            if len(names) == 1:
                translated_ids = list(map(tmap[names[0]].get, translatable))
            else:
                translated_ids = [tmap[n].get(idx) for n, idx in zip(names, translatable)]

            translatable.update(pd.Series(translated_ids, index=translatable.index))

        return translatable if copy else None
