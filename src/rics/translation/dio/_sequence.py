from typing import Any, Dict, List, Optional, Sequence, TypeVar

import numpy as np

from rics.translation.dio import DataStructureIO
from rics.translation.dio.exceptions import NotInplaceTranslatableError
from rics.translation.offline import TranslationMap
from rics.translation.types import IdType, NameType

T = TypeVar("T", list, np.ndarray, tuple)


class SequenceIO(DataStructureIO):
    """Implementation for numpy arrays, Python lists and tuples."""

    @staticmethod
    def handles_type(arg: Any) -> bool:
        return isinstance(arg, (list, np.ndarray, tuple))

    @staticmethod
    def extract(translatable: T, names: List[NameType]) -> Dict[NameType, Sequence[IdType]]:
        if len(names) != 1:
            raise ValueError("Length of names must be one.")

        return {names[0]: list(translatable)}

    @staticmethod
    def insert(translatable: T, names: List[NameType], tmap: TranslationMap, copy: bool) -> Optional[T]:
        t = translate_sequence(translatable, names, tmap)

        if copy:
            clazz = np.array if isinstance(translatable, np.ndarray) else type(translatable)
            return clazz(t)

        try:
            translatable[:] = t[:]  # type: ignore
            return None
        except TypeError as e:
            raise NotInplaceTranslatableError(translatable) from e


def translate_sequence(s: T, names: List[NameType], tmap: TranslationMap) -> List[Optional[str]]:
    """Return a translated copy of the sequence `s`."""
    if len(names) == 1:
        return list(map(tmap[names[0]].get, s))
    elif len(names) == len(s):
        return [tmap[n].get(idx) for n, idx in zip(names, s)]
    else:
        raise ValueError(
            f"Number of names {len(names)} must be one or equal to the length of the data {len(s)} to "
            f"translate, but got {names=}."
        )
