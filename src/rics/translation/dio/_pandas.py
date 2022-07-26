from typing import Any, Dict, List, Optional, Sequence, TypeVar

import pandas as pd

from rics.translation.dio._data_structure_io import DataStructureIO
from rics.translation.dio._sequence import SequenceIO, translate_sequence, verify_names
from rics.translation.offline import TranslationMap
from rics.translation.types import IdType, NameType

T = TypeVar("T", pd.DataFrame, pd.Series)


class PandasIO(DataStructureIO):
    """Implementation for Pandas data types."""

    @staticmethod
    def handles_type(arg: Any) -> bool:
        return isinstance(arg, (pd.DataFrame, pd.Series))

    @staticmethod
    def extract(translatable: T, names: List[NameType]) -> Dict[NameType, Sequence[IdType]]:
        if isinstance(translatable, pd.DataFrame):
            return translatable[names].to_dict(orient="list")
        else:
            return SequenceIO.extract(translatable, names)

    @staticmethod
    def insert(translatable: T, names: List[NameType], tmap: TranslationMap, copy: bool) -> Optional[T]:
        translatable = translatable.copy() if copy else translatable

        if isinstance(translatable, pd.DataFrame):
            for name in names:
                translatable[name] = translatable[name].map(tmap[name].get)
        else:
            verify_names(len(translatable), names)
            translatable.update(pd.Series(translate_sequence(translatable, names, tmap), index=translatable.index))

        return translatable if copy else None
