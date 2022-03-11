from typing import Any, Dict, List, Optional, Sequence, TypeVar

from rics.translation.dio._data_structure_io import DataStructureIO
from rics.translation.offline import TranslationMap
from rics.translation.offline.types import IdType, NameType

T = TypeVar("T", bound=Dict)


class DictIO(DataStructureIO):
    """Implementation for dicts."""

    @staticmethod
    def handles_type(arg: Any) -> bool:
        """Return True if the implementation handles data for the type of `arg`."""
        return isinstance(arg, dict)

    @staticmethod
    def extract(translatable: T, names: List[NameType]) -> Dict[NameType, Sequence[IdType]]:
        """Extract IDs from a dict `translatable`."""
        return {name: translatable[name] for name in names}

    @staticmethod
    def insert(translatable: T, names: List[NameType], tmap: TranslationMap, copy: bool) -> Optional[T]:
        """Insert translations into a dict."""
        translatable = dict(translatable) if copy else translatable  # type: ignore

        for name in filter(translatable.__contains__, names):
            translatable[name] = type(translatable[name])(map(tmap[name].get, translatable[name]))

        return translatable if copy else None
