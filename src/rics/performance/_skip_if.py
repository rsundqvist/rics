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
    """Estimated time for all repetitions over the whole stratum of `data_label`, not just this variant.

    ``None`` during calibration, and when ``number`` is given explicitly.
    """
    results_so_far: ResultsDict
    """The run's live results, ``{candidate_label: {data_label: [runtime, ...]}}``. Empty during calibration."""


SkipIfFunc: TypeAlias = Callable[[SkipIfParams[DataType, *Ts]], bool]
"""A predicate ``(SkipIfParams) -> bool``; return ``True`` to exclude a ``(candidate, data)`` combination."""
