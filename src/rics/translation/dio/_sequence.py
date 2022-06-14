from typing import Any, Dict, List, Optional, Sequence, TypeVar

import numpy as np

from rics.translation.dio import DataStructureIO
from rics.translation.dio.exceptions import NotInplaceTranslatableError
from rics.translation.offline import TranslationMap
from rics.translation.offline.types import IdType, NameType

T = TypeVar("T", list, np.ndarray, tuple)


class SequenceIO(DataStructureIO):
    """Implementation for numpy arrays, Python lists and tuples."""

    @staticmethod
    def handles_type(arg: Any) -> bool:
        """Return True if the implementation handles data for the type of `arg`."""
        return isinstance(arg, (list, np.ndarray, tuple))

    @staticmethod
    def extract(translatable: T, names: List[NameType]) -> Dict[NameType, Sequence[IdType]]:
        """Extract IDs from an array `translatable`."""
        if len(names) != 1:
            raise ValueError("Length of names must be one.")

        return {names[0]: list(translatable)}

    @staticmethod
    def insert(translatable: T, names: List[NameType], tmap: TranslationMap, copy: bool) -> Optional[T]:
        """Insert translations into an array."""
        clazz = np.array if isinstance(translatable, np.ndarray) else type(translatable)

        if len(names) == 1:
            copied = clazz(list(map(tmap[names[0]].__getitem__, translatable)))
        else:
            # TODO
            copied = clazz(list(map(tmap[names[0]].__getitem__, translatable)))

        if copy:
            return copied

        try:
            translatable[:] = copied[:]  # type: ignore
            return None
        except TypeError as e:
            raise NotInplaceTranslatableError(translatable) from e
