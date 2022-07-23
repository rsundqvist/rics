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
        verify_names(len(translatable), names)
        return {names[0]: list(translatable)} if len(names) == 1 else {n: list(r) for n, r in zip(names, translatable)}

    @staticmethod
    def insert(translatable: T, names: List[NameType], tmap: TranslationMap, copy: bool) -> Optional[T]:
        verify_names(len(translatable), names)
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
    return list(map(tmap[names[0]].get, s)) if len(names) == 1 else [tmap[n].get(idx) for n, idx in zip(names, s)]


def verify_names(data_len: int, names: List[NameType]) -> None:
    """Verify that the length of names is either 1 or equal to the length of the data."""
    num_names = len(names)
    if num_names != 1 and num_names != data_len:
        raise ValueError(
            f"Number of names {len(names)} must be 1 or equal to the length of the data ({data_len}) to "
            f"translate, but got {names=}."
        )
