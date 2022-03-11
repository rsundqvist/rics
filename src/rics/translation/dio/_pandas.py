from typing import Any, Dict, List, Optional, Sequence, TypeVar

import pandas as pd

from rics.translation.dio import exceptions
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
            PandasIO._check_names(names, translatable)
            return translatable

    @staticmethod
    def insert(translatable: T, names: List[NameType], tmap: TranslationMap, copy: bool) -> Optional[T]:
        """Insert translations into a Pandas type."""
        if not copy and isinstance(translatable, pd.Series):
            raise exceptions.NotInplaceTranslatableError(translatable)

        translatable = translatable.copy() if copy else translatable

        if isinstance(translatable, pd.DataFrame):
            for name in names:
                translatable[name] = translatable[name].map(tmap[name])
        else:
            PandasIO._check_names(names, translatable)
            return translatable

        return translatable if copy else None

    @staticmethod
    def _check_names(names: Sequence[NameType], nd: T) -> None:
        if len(names) > 1:
            raise ValueError("Must have at most one name for Series types.")
        if nd.name is not None and len(names) == 1 and nd.name != names[0]:
            raise ValueError("Name mismatch.")
