"""Functions and classes used by the ``Mapper`` for handling score matrices.

.. warning::

   This module is considered an implementation detail, and may change without notice.
"""

import logging
import warnings
from collections import defaultdict as _defaultdict
from contextlib import contextmanager as _contextmanager
from dataclasses import dataclass as _dataclass
from typing import Dict, Generator, Generic as _Generic, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

from rics.mapping import Cardinality as _Cardinality, DirectionalMapping as _DirectionalMapping
from rics.mapping.types import CandidateType, ValueType

_MAPPER_LOGGER = logging.getLogger(__package__).getChild("Mapper")
ACCEPT_LOGGER = _MAPPER_LOGGER.getChild("accept")
SUPERSESSION_LOGGER = ACCEPT_LOGGER.getChild("details")
UNMAPPED_LOGGER = _MAPPER_LOGGER.getChild("unmapped").getChild("details")

warnings.warn("This module is considered an implementation detail, and may change without notice.", UserWarning)


@_contextmanager
def enable_verbose_debug_messages() -> Generator[None, None, None]:  # typing.ContextManager doesn't work?
    """Temporarily enable verbose DEBUG-level messages."""
    from rics.mapping import filter_functions, heuristic_functions, score_functions

    before = filter_functions.VERBOSE, heuristic_functions.VERBOSE, score_functions.VERBOSE
    try:
        filter_functions.VERBOSE, heuristic_functions.VERBOSE, score_functions.VERBOSE = True, True, True
        yield
    finally:
        filter_functions.VERBOSE, heuristic_functions.VERBOSE, score_functions.VERBOSE = before


class MatchScores:
    """High-level selection operations.

    Args:
        scores: A score matrix, where ``scores.index`` are values and ``score.columns`` are treated as the candidates.
        min_score: Minimum score to consider make a `value -> candidate` match.
    """

    def __init__(self, scores: pd.DataFrame, min_score: float) -> None:
        self._min_score = min_score
        self._matrix = scores

    def to_directional_mapping(self, cardinality: _Cardinality = None) -> _DirectionalMapping[ValueType, CandidateType]:
        """Create a ``DirectionalMapping`` with a given target ``Cardinality``.

        Args:
            cardinality: Explicit cardinality to set, see :attr:`~rics.mapping.DirectionalMapping.cardinality`. If
                ``None``, use the actual cardinality when selecting all matches with scores :attr:`above` the minimum.

        Returns:
            A ``DirectionalMapping``.
        """
        matches: List[MatchScores.Record[ValueType, CandidateType]]
        rejections: List[MatchScores.Reject[ValueType, CandidateType]]
        matches, rejections = self._match(cardinality)

        left_to_right = _defaultdict(list)
        for record in list(matches):
            supersedes: List[MatchScores.Reject] = []
            if SUPERSESSION_LOGGER.isEnabledFor(logging.DEBUG) and rejections:
                for rr in rejections:
                    if record in (rr.superseding_value, rr.superseding_candidate):
                        supersedes.append(rr)

            if ACCEPT_LOGGER.isEnabledFor(logging.INFO):
                reason = "(short-circuit or override)" if record.score == np.inf else f">= {self._min_score}"
                ACCEPT_LOGGER.debug(f"Accepted: {record} {reason}.")

            if supersedes:
                s = "\n".join("    " + rr.explain(self._min_score) for rr in supersedes)
                SUPERSESSION_LOGGER.debug(f"This match supersedes {len(supersedes)} other matches:\n{s}")

            left_to_right[record.value].append(record.candidate)

        if rejections and UNMAPPED_LOGGER.isEnabledFor(logging.DEBUG):
            unmapped_values = set(self._matrix.index.difference(left_to_right))
            for value in unmapped_values:
                lst = []
                for rr in filter(lambda r: r.record.value == value, rejections):  # noqa: B023
                    lst.append(f"    {rr.explain(self._min_score, full=True)}")
                value_reasons = "\n".join(lst)
                UNMAPPED_LOGGER.debug(f"Could not map {value=}:\n{value_reasons}")

        return _DirectionalMapping(
            cardinality=cardinality,
            left_to_right={value: tuple(matches) for value, matches in left_to_right.items()},
            _verify=False,
        )

    def _match(
        self, cardinality: _Cardinality = None
    ) -> Tuple[List["Record[ValueType, CandidateType]"], List["Reject[ValueType, CandidateType]"]]:
        rejections: Optional[List[MatchScores.Reject]] = None
        records: List[MatchScores.Record] = self.above

        if SUPERSESSION_LOGGER.isEnabledFor(logging.DEBUG) or UNMAPPED_LOGGER.isEnabledFor(logging.DEBUG):
            rejections = []
            records += self.below

        if cardinality is _Cardinality.OneToOne:
            matches = self._select_one_to_one(records, rejections)
        elif cardinality is _Cardinality.OneToMany:
            matches = self._select_one_to_many(records, rejections)
        elif cardinality is _Cardinality.ManyToOne:
            matches = self._select_many_to_one(records, rejections)
        else:
            matches = self._select_many_to_many(records, rejections)

        return list(matches), rejections or []

    def _get_sorted(self) -> pd.Series:
        sorted_scores: pd.Series = self._matrix.stack()
        sorted_scores.sort_values(ascending=False, inplace=True)
        return sorted_scores

    @property
    def above(self) -> List["Record"]:
        """Get all records with scores `above` the threshold."""
        s = self._get_sorted()
        return self._from_series(s[s >= self._min_score])

    @property
    def below(self) -> List["Record"]:
        """Get all records with scores `below` the threshold."""
        s = self._get_sorted()
        return self._from_series(s[s < self._min_score])

    @_dataclass(frozen=True)
    class Record(_Generic[ValueType, CandidateType]):
        """Data concerning a match."""

        value: ValueType
        """A hashable value."""
        candidate: CandidateType
        """A hashable candidate."""
        score: float
        """Likeness score computed by some scoring function."""

        def __str__(self) -> str:
            return f"{repr(self.value)} -> '{self.candidate}'; score={self.score:.3f}"

    @classmethod
    def _from_series(cls, s: pd.Series) -> List[Record[ValueType, CandidateType]]:
        return [MatchScores.Record(value, candidate, score) for (value, candidate), score in s.iteritems()]

    @_dataclass(frozen=True)
    class Reject(_Generic[ValueType, CandidateType]):
        """Data concerning the rejection of a match."""

        record: "MatchScores.Record[ValueType, CandidateType]"
        superseding_value: Optional["MatchScores.Record[ValueType, CandidateType]"] = None
        superseding_candidate: Optional["MatchScores.Record[ValueType, CandidateType]"] = None

        def explain(self, min_score: float, full: bool = False) -> str:  # pragma: no cover
            """Create a string which explains the rejection.

            Args:
                min_score: Minimum score to accept a match.
                full: If ``True`` show full information about superseding matches.

            Returns:
                An explanatory string.
            """
            if self.record.score == -np.inf:
                if self.superseding_value and self.superseding_value.score == np.inf:
                    extra = f": {self.superseding_value}" if full else ""
                    why = f" (superseded by short-circuit or override{extra})"
                elif self.superseding_candidate and self.superseding_candidate.score == np.inf:
                    extra = f": {self.superseding_candidate}" if full else ""
                    why = f" (superseded by short-circuit or override{extra}"
                else:
                    why = " (filtered)"
            elif self.record.score < min_score:
                why = f" < {min_score} (below threshold)"
            else:
                ands = []
                if self.superseding_value:
                    extra = f": {self.superseding_value}" if full else ""
                    ands.append(f"value={repr(self.superseding_value.value)}{extra}")
                if self.superseding_candidate:
                    extra = f": {self.superseding_candidate}" if full else ""
                    ands.append(f"candidate={repr(self.superseding_candidate.candidate)}{extra}")
                why = f" (superseded on {' and '.join(ands)})"

            return f"{self.record}{why}."

    def _select_one_to_one(
        self,
        records: Iterable[Record[ValueType, CandidateType]],
        rejections: List[Reject[ValueType, CandidateType]] = None,
    ) -> Iterable[Record[ValueType, CandidateType]]:
        mvs: Dict[ValueType, MatchScores.Record[ValueType, CandidateType]] = {}
        mcs: Dict[CandidateType, MatchScores.Record[ValueType, CandidateType]] = {}

        for record in records:
            if record.score < self._min_score or record.value in mvs or record.candidate in mcs:
                if rejections is not None:  # pragma: no cover
                    rejections.append(
                        MatchScores.Reject(
                            record,
                            superseding_value=mvs.get(record.value),
                            superseding_candidate=mcs.get(record.candidate),
                        )
                    )
                continue
            mvs[record.value] = record
            mcs[record.candidate] = record
            yield record

    def _select_one_to_many(
        self,
        records: Iterable[Record[ValueType, CandidateType]],
        rejections: List[Reject[ValueType, CandidateType]] = None,
    ) -> Iterable[Record[ValueType, CandidateType]]:
        mcs: Dict[CandidateType, MatchScores.Record[ValueType, CandidateType]] = {}

        for record in records:
            if record.score < self._min_score or record.candidate in mcs:
                if rejections is not None:  # pragma: no cover
                    rejections.append(MatchScores.Reject(record, superseding_candidate=mcs.get(record.candidate)))
                continue
            mcs[record.candidate] = record
            yield record

    def _select_many_to_one(
        self,
        records: Iterable[Record[ValueType, CandidateType]],
        rejections: List[Reject[ValueType, CandidateType]] = None,
    ) -> Iterable[Record[ValueType, CandidateType]]:
        mvs: Dict[ValueType, MatchScores.Record[ValueType, CandidateType]] = {}

        for record in records:
            if record.score < self._min_score or record.value in mvs:
                if rejections is not None:  # pragma: no cover
                    rejections.append(MatchScores.Reject(record, superseding_value=mvs.get(record.value)))
                continue
            mvs[record.value] = record
            yield record

    def _select_many_to_many(
        self,
        records: Iterable[Record[ValueType, CandidateType]],
        rejections: List[Reject[ValueType, CandidateType]] = None,
    ) -> Iterable[Record[ValueType, CandidateType]]:
        for record in records:  # pragma: no cover
            if record.score < self._min_score:
                if rejections is not None:
                    rejections.append(MatchScores.Reject(record))
                continue
            yield record
