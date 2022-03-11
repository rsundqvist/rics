import logging
from typing import Any, Dict, Generic, Hashable, Iterable, Literal, Optional, Set, Tuple, TypeVar, Union

from rics.cardinality import Cardinality, CardinalityType
from rics.mapping._directional_mapping import DirectionalMapping
from rics.mapping.exceptions import MappingError
from rics.mapping.score_functions import MappingScoreFunction, NamesLiteral
from rics.mapping.score_functions import get as from_name
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
        min_score: Minimum score `s_i`, as given by ``score(k, c_i)``, to consider `k` a match for `c_i`.
        overrides: User-defined 1:1 mappings which (`value` to `candidate`) override the scoring logic.
        cardinality: Desired cardinality for mapped values. None=derive.
    """

    def __init__(
        self,
        candidates: Iterable[CandidateType] = None,
        score_function: Union[NamesLiteral, MappingScoreFunction] = "equality",
        min_score: float = 1.00,
        overrides: Dict[ValueType, CandidateType] = None,
        unmapped_values_action: Literal["raise", "ignore"] = "ignore",
        cardinality: Optional[CardinalityType] = Cardinality.OneToOne,
        **score_function_kwargs: Any,
    ) -> None:
        self.candidates = set(candidates or [])
        self._score = score_function if callable(score_function) else from_name(score_function)
        self._min_score = min_score
        self._fixed = {} if overrides is None else {k: (v,) for k, v in overrides.items()}
        if unmapped_values_action not in ("raise", "ignore"):
            raise ValueError(f"{unmapped_values_action=} not in ('raise', 'ignore').")  # pragma: no cover
        self._unmapped_action = unmapped_values_action
        self._cardinality = None if cardinality is None else Cardinality.parse(cardinality, strict=True)
        self._score_kwargs = score_function_kwargs

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "Mapper":
        """Create instance from a dict.

        Args:
            config: Dict configuration.

        Returns:
            A new instance.
        """
        return Mapper(**config)

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
        """
        left_to_right: Dict[ValueType, MatchTuple] = {
            value: self._fixed[value] for value in filter(self._fixed.__contains__, values)
        }
        for value in set(values).difference(left_to_right):
            matches = self._process_matches(self._map_value(value), value)
            if matches:
                left_to_right[value] = matches

        return DirectionalMapping(
            cardinality=self._cardinality,
            left_to_right=left_to_right,
            _verify=True,
        )

    def _process_matches(self, matches: Iterable[CandidateType], value: ValueType) -> MatchTuple:
        ans = tuple(matches)

        if not ans:
            msg = f"Could not map {repr(value)} to any of {self.candidates}."
            LOGGER.debug(msg)
            if self._unmapped_action == "raise":
                raise MappingError(msg)

        return ans

    def _map_value(self, value: ValueType) -> Iterable[CandidateType]:
        """Map a single value against candidates.

        Args:
            value: An element to find matches for.

        Yields:
            Matching candidates sorted by decreasing score.
        """
        scores = self._score(value, self._candidates, **self._score_kwargs)
        sorted_candidates = sorted(zip(scores, self._candidates), key=lambda t: -t[0])
        for score, candidate in sorted_candidates:
            if score >= self._min_score:
                yield candidate

                if LOGGER.isEnabledFor(logging.DEBUG):
                    extra = "" if self._cardinality == Cardinality.OneToOne else " Looking for more matches.."
                    LOGGER.debug(
                        f"Mapped: {repr(value)} -> {repr(candidate)}, {score=:2.3f} > {self._min_score}.{extra}"
                    )

                if self._cardinality == Cardinality.OneToOne:
                    break
            elif LOGGER.isEnabledFor(logging.DEBUG):
                LOGGER.debug(f"Rejected: {repr(value)} -> {repr(candidate)}, {score=:.3f} < {self._min_score}.")

    def __repr__(self) -> str:
        candidates = self._candidates
        return f"{tname(self)}(score={self._score} >= {self._min_score}, {candidates=})"
