from typing import Any, Dict, List, Sequence

from rics.translation.dio import DataStructureIO
from rics.translation.dio.exceptions import NotInplaceTranslatableError
from rics.translation.offline import TranslationMap
from rics.translation.types import IdType, NameType


class SingleValueIO(DataStructureIO):
    """Implementation for non-iterables. And strings."""

    @staticmethod
    def handles_type(arg: Any) -> bool:
        return isinstance(arg, (int, str))

    @staticmethod
    def extract(translatable: IdType, names: List[NameType]) -> Dict[NameType, Sequence[IdType]]:
        if len(names) != 1:  # pragma: no cover
            raise ValueError("Length of names must be one.")

        return {names[0]: (translatable,)}

    @staticmethod
    def insert(translatable: IdType, names: List[NameType], tmap: TranslationMap, copy: bool) -> str:
        if not copy:  # pragma: no cover
            raise NotInplaceTranslatableError(translatable)

        return tmap[names[0]][translatable]
