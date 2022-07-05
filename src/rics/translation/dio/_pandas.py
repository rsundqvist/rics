from typing import Any, Dict, List, Optional, Sequence, TypeVar

import pandas as pd

from rics.translation.dio._data_structure_io import DataStructureIO
from rics.translation.dio._sequence import translate_sequence
from rics.translation.offline import TranslationMap
from rics.translation.types import IdType, NameType

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
            return {names[0]: translatable}

    @staticmethod
    def insert(translatable: T, names: List[NameType], tmap: TranslationMap, copy: bool) -> Optional[T]:
        """Insert translations into a Pandas type."""
        translatable = translatable.copy() if copy else translatable

        if isinstance(translatable, pd.DataFrame):
            for name in names:
                translatable[name] = translatable[name].map(tmap[name].get)
        else:
            translatable.update(pd.Series(translate_sequence(translatable, names, tmap), index=translatable.index))

        return translatable if copy else None
