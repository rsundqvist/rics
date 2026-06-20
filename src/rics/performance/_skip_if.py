from collections.abc import Callable, Hashable
from dataclasses import dataclass
from typing import Generic, TypeAlias

from .types import CandFunc, DataType, ResultsDict, Ts


@dataclass(frozen=True)
class SkipIfParams(Generic[DataType, *Ts]):
    """Data type for a `skip_if` predicate."""

    candidate: CandFunc[DataType]
    """Current candidate function."""
    candidate_label: str
    """Candidate label."""
    data: DataType
    """Current data."""
    data_label: Hashable | tuple[*Ts]
    """Data label."""
    est_time: float | None
    """Estimated time to finish all repetitions. Only when `number` is derived."""
    results_so_far: ResultsDict
    """A snapshot timing values."""


SkipIfFunc: TypeAlias = Callable[[SkipIfParams[DataType, *Ts]], bool]
"""A predicate ``(SkipIfParams) -> bool``; return ``True`` to exclude a ``(candidate, data)`` combination."""
