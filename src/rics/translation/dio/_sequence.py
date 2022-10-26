from typing import Any, Callable, Dict, List, Optional, Sequence, TypeVar

import numpy as np
import pandas as pd

from rics.translation.dio import DataStructureIO
from rics.translation.dio.exceptions import NotInplaceTranslatableError
from rics.translation.offline import TranslationMap
from rics.translation.types import IdType, NameType, SourceType
from rics.utility.collections.misc import as_list

T = TypeVar("T", list, np.ndarray, tuple, pd.Index)  # type: ignore[type-arg]  # TODO: Higher-Kinded TypeVars


class SequenceIO(DataStructureIO):
    """Implementation for numpy arrays, Python lists and tuples."""

    @staticmethod
    def handles_type(arg: Any) -> bool:
        return isinstance(arg, (list, np.ndarray, tuple, pd.Index))

    @staticmethod
    def extract(translatable: T, names: List[NameType]) -> Dict[NameType, Sequence[IdType]]:
        verify_names(len(translatable), names)
        return (
            {names[0]: as_list(translatable)}
            if len(names) == 1
            else {n: as_list(r) for n, r in zip(names, translatable)}
        )

    @staticmethod
    def insert(
        translatable: T, names: List[NameType], tmap: TranslationMap[NameType, SourceType, IdType], copy: bool
    ) -> Optional[T]:
        verify_names(len(translatable), names)
        t = translate_sequence(translatable, names, tmap)

        ctor: Callable[[List[Optional[str]]], T]
        if copy:
            if isinstance(translatable, pd.Index):
                ctor = pd.Index
            elif isinstance(translatable, np.ndarray):
                ctor = np.array
            else:
                ctor = type(translatable)
            return ctor(t)

        try:
            translatable[:] = t[:]  # type: ignore
            return None
        except TypeError as e:
            raise NotInplaceTranslatableError(translatable) from e


def translate_sequence(
    s: T, names: List[NameType], tmap: TranslationMap[NameType, SourceType, IdType]
) -> List[Optional[str]]:
    """Return a translated copy of the sequence `s`."""
    if len(names) == 1:
        return list(map(tmap[names[0]].get, s))

    return [
        translate_sequence(element, [name], tmap)  # type: ignore
        if SequenceIO.handles_type(element)
        else tmap[name].get(element)
        for name, element in zip(names, s)
    ]


def verify_names(data_len: int, names: List[NameType]) -> None:  # pragma: no cover
    """Verify that the length of names is either 1 or equal to the length of the data."""
    num_names = len(names)
    if num_names != 1 and num_names != data_len:
        raise ValueError(
            f"Number of names {len(names)} must be 1 or equal to the length of the data ({data_len}) to "
            f"translate, but got {names=}."
        )
