import logging
from typing import Any, Dict, Generic, Hashable, Iterable, List, Literal, Optional, Set, Tuple, TypeVar, Union

from rics.cardinality import Cardinality, CardinalityType
from rics.mapping import exceptions
from rics.mapping import filter_functions as mf
from rics.mapping._directional_mapping import DirectionalMapping
from rics.mapping.exceptions import MappingError
from rics.mapping.score_functions import MappingScoreFunction, from_name
from rics.utility.misc import tname

ValueType = TypeVar("ValueType", bound=Hashable)
CandidateType = TypeVar("CandidateType", bound=Hashable)
MatchTuple = Tuple[CandidateType, ...]

LOGGER = logging.getLogger(__package__).getChild("Mapper")


class Mapper(Generic[ValueType, CandidateType]):
    """Map candidates (right side) to values (left side).

    A ``Mapper`` creates :class:`~rics.mapping.BidirectionalMapping`-instances from collections of
    candidates for sets of values passed to :meth:`apply`.

    Args:
        candidates: Possible items for values to be matched with.
        score_function: A callable which accepts a value `k` and an ordered collection of candidates `c`, returning a
            score ``s_i`` for each candidate `c_i` in `c`. Default: ``s_i = float(k == c_i)``. Higher=better match.
        score_function_kwargs: Keyword arguments for `score_function`.
        filter_functions: Function-kwargs pairs of filters to apply before scoring.
        min_score: Minimum score `s_i`, as given by ``score(k, c_i)``, to consider `k` a match for `c_i`.
        overrides: User-defined 1:1 mappings which (`value` to `candidate`) override the scoring logic.
        unmapped_values_action: Action to take if mapping fails.
        cardinality: Desired cardinality for mapped values. None=derive.
    """

    def __init__(
        self,
        candidates: Iterable[CandidateType] = None,
        score_function: Union[str, MappingScoreFunction] = "equality",
        score_function_kwargs: Dict[str, Any] = None,
        filter_functions: Iterable[Tuple[Union[str, mf.FilterFunction], Dict[str, Any]]] = (),
        min_score: float = 1.00,
        overrides: Dict[ValueType, CandidateType] = None,
        unmapped_values_action: Literal["raise", "ignore"] = "ignore",
        cardinality: Optional[CardinalityType] = Cardinality.OneToOne,
    ) -> None:
        self.candidates = set(candidates or [])
        self._score = score_function if callable(score_function) else from_name(score_function)
        self._score_kwargs = score_function_kwargs or {}
        self._min_score = min_score
        self._fixed = {} if overrides is None else {k: (v,) for k, v in overrides.items()}
        if unmapped_values_action not in ("raise", "ignore"):
            raise ValueError(f"{unmapped_values_action=} not in ('raise', 'ignore').")  # pragma: no cover
        self._unmapped_action = unmapped_values_action
        self._cardinality = None if cardinality is None else Cardinality.parse(cardinality, strict=True)
        self._filters: List[Tuple[mf.FilterFunction, Dict[str, Any]]] = [
            ((getattr(mf, func) if isinstance(func, str) else func), kwargs) for func, kwargs in filter_functions
        ]

    @property
    def candidates(self) -> Set[CandidateType]:
        """Candidates to match with when `apply` is called."""
        return self._candidates

    @candidates.setter
    def candidates(self, values: Set[CandidateType]) -> None:
        self._candidates = values

    def apply(self, values: Iterable[ValueType]) -> DirectionalMapping:
        """Map values to candidates.

        Args:
            values: Iterable of elements to match to candidates.

        Returns:
            A ``BidirectionalMapping`` with values on the left side and candidates on the right.

        Raises:
            MappingError: If any values failed to match and ``unmapped_values_action='raise'``.
            BadFilterError: If a filter returns candidates that are not a subset of the original candidates.
        """
        left_to_right: Dict[ValueType, MatchTuple] = {
            value: self._fixed[value] for value in filter(self._fixed.__contains__, values)
        }
        for value in set(values).difference(left_to_right):
            matches = self._map_value(value)
            if matches is None:
                continue  # All candidates removed by filtering
            if matches:
                left_to_right[value] = matches
            else:
                msg = f"Could not map {repr(value)} to any of {self.candidates}."
                LOGGER.debug(msg)
                if self._unmapped_action == "raise":
                    raise MappingError(msg)

        return DirectionalMapping(
            cardinality=self._cardinality,
            left_to_right=left_to_right,
            _verify=True,
        )

    def _map_value(self, value: ValueType) -> Optional[MatchTuple]:
        scores = self._score(value, self._candidates, **self._score_kwargs)
        sorted_candidates = sorted(zip(scores, self._candidates), key=lambda t: -t[0])

        filtered_candidates = set(self._candidates)
        for filter_function, kwargs in self._filters:
            filtered_candidates = filter_function(value, filtered_candidates, **kwargs)

            not_in_original_candidates = filtered_candidates.difference(self._candidates)
            if not_in_original_candidates:
                raise exceptions.BadFilterError(
                    f"Filter {tname(filter_function)}({value}, candidates, **{kwargs}) created new"
                    f"candidates: {not_in_original_candidates}"
                )

            if not filtered_candidates:
                return None

        ans = []
        for score, candidate in sorted_candidates:
            if candidate not in filtered_candidates:
                score = -float("inf")

            if score >= self._min_score:
                ans.append(candidate)

                if LOGGER.isEnabledFor(logging.DEBUG):
                    extra = "" if self._cardinality == Cardinality.OneToOne else " Looking for more matches.."
                    LOGGER.debug(
                        f"Mapped: {repr(value)} -> {repr(candidate)}, {score=:2.3f} > {self._min_score}.{extra}"
                    )

                if self._cardinality == Cardinality.OneToOne:
                    break
            elif LOGGER.isEnabledFor(logging.DEBUG):
                extra = " (removed by filters)" if score == -float("inf") else ""
                LOGGER.debug(f"Rejected: {repr(value)} -> {repr(candidate)}, {score=:.3f} < {self._min_score}{extra}.")

        return tuple(ans)

    def __repr__(self) -> str:
        candidates = self._candidates
        score = tname(self._score)
        return f"{tname(self)}({score=} >= {self._min_score}, {len(self._filters)} filters, {candidates=})"

    def copy(self) -> "Mapper":
        """Make a copy of this Mapper."""
        return Mapper(
            candidates=self.candidates,
            score_function=self._score,
            score_function_kwargs=self._score_kwargs.copy(),
            filter_functions=[(func, kwargs.copy()) for func, kwargs in self._filters],
            min_score=self._min_score,
            overrides=None if self._fixed is None else {k: v[0] for k, v in self._fixed.items()},
            unmapped_values_action=self._unmapped_action,
            cardinality=self._cardinality,
        )
