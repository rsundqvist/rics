import logging
import warnings
from typing import Any, Dict, Generic, Hashable, Iterable, List, Optional, Set, Tuple, TypeVar, Union

from rics.cardinality import Cardinality, CardinalityType
from rics.mapping import exceptions
from rics.mapping import filter_functions as mf
from rics.mapping._directional_mapping import DirectionalMapping
from rics.mapping.exceptions import MappingError, MappingWarning
from rics.mapping.score_functions import ScoreFunction, from_name
from rics.utility.action_level import ActionLevel, ActionLevelTypes
from rics.utility.collections import InheritedKeysDict
from rics.utility.misc import tname

ContextType = TypeVar("ContextType", bound=Hashable)
ValueType = TypeVar("ValueType", bound=Hashable)
CandidateType = TypeVar("CandidateType", bound=Hashable)
MatchTuple = Tuple[CandidateType, ...]

LOGGER = logging.getLogger(__package__).getChild("Mapper")


class Mapper(Generic[ContextType, ValueType, CandidateType]):
    """Map candidates (right side) to values (left side).

    A ``Mapper`` creates :class:`~rics.mapping.BidirectionalMapping`-instances from collections of
    candidates for sets of values passed to :meth:`apply`.

    Args:
        score_function: A callable which accepts a value `k` and an ordered collection of candidates `c`, returning a
            score ``s_i`` for each candidate `c_i` in `c`. Default: ``s_i = float(k == c_i)``. Higher=better match.
        score_function_kwargs: Keyword arguments for `score_function`.
        filter_functions: Function-kwargs pairs of filters to apply before scoring.
        min_score: Minimum score `s_i`, as given by ``score(k, c_i)``, to consider `k` a match for `c_i`.
        overrides: If a dict, assumed to be 1:1 mappings which (`value` to `candidate`) override the scoring logic. If
            :class:`~rics.utility.collections.InheritedKeysDict`, the context passed to :meth:`apply` will be used to
            retrieve the actual overrides.
        unmapped_values_action: Action to take if mapping fails.
        cardinality: Desired cardinality for mapped values. None=derive.
    """

    def __init__(
        self,
        score_function: Union[str, ScoreFunction] = "equality",
        score_function_kwargs: Dict[str, Any] = None,
        filter_functions: Iterable[Tuple[Union[str, mf.FilterFunction], Dict[str, Any]]] = (),
        min_score: float = 1.00,
        overrides: Union[
            InheritedKeysDict[ContextType, ValueType, CandidateType], Dict[ValueType, CandidateType]
        ] = None,
        unmapped_values_action: ActionLevelTypes = "ignore",
        cardinality: Optional[CardinalityType] = Cardinality.ManyToOne,
    ) -> None:
        self._score = score_function if callable(score_function) else from_name(score_function)
        self._score_kwargs = score_function_kwargs or {}
        self._min_score = min_score
        self._overrides: Union[InheritedKeysDict, Dict[ValueType, CandidateType]] = (
            overrides if isinstance(overrides, InheritedKeysDict) else (overrides or {})
        )
        self._context_sensitive_overrides = isinstance(self._overrides, InheritedKeysDict)
        self._unmapped_action: ActionLevel = ActionLevel.verify(unmapped_values_action)
        self._cardinality = None if cardinality is None else Cardinality.parse(cardinality, strict=True)
        self._filters: List[Tuple[mf.FilterFunction, Dict[str, Any]]] = [
            ((getattr(mf, func) if isinstance(func, str) else func), kwargs) for func, kwargs in filter_functions
        ]

    def apply(
        self,
        values: Iterable[ValueType],
        candidates: Iterable[CandidateType],
        context: ContextType = None,
        **kwargs: Any,
    ) -> DirectionalMapping:
        """Map values to candidates.

        Args:
            values: Iterable of elements to match to candidates.
            candidates: Iterable of candidates to match with `value`. Duplicate elements will be discarded.
            context: Context in which mapping is being done.
            kwargs: Runtime keyword arguments for score and filter functions. May be used to add information which is
                not known when the mapper is initialized.

        Returns:
            A ``BidirectionalMapping`` with values on the left side and candidates on the right.

        Raises:
            MappingError: If any values failed to match and ``unmapped_values_action='raise'``.
            BadFilterError: If a filter returns candidates that are not a subset of the original candidates.
        """
        candidates = set(candidates)
        values = set(values)
        left_to_right = self._create_l2r(values, context)

        extra = f" in {context=}" if context else ""

        for value in values.difference(left_to_right):
            LOGGER.debug(f"Begin mapping {value=}{extra} to {candidates=} using {self._score}.")
            matches = self._map_value(value, candidates, context, kwargs)
            if matches is None:
                continue  # All candidates removed by filtering
            if matches:
                left_to_right[value] = matches
            else:  # pragma: no cover
                msg = f"Could not map {value=}{extra} to any of {candidates=}."
                if self._unmapped_action is ActionLevel.RAISE:
                    LOGGER.error(msg)
                    raise MappingError(msg)
                elif self._unmapped_action is ActionLevel.WARN:
                    LOGGER.warning(msg)
                    warnings.warn(msg, MappingWarning)
                else:
                    LOGGER.debug(msg)

        return DirectionalMapping(
            cardinality=self._cardinality,
            left_to_right=left_to_right,
            _verify=True,
        )

    @property
    def context_sensitive_overrides(self) -> bool:
        """Return True if overrides are of type :class:`.InheritedKeysDict`."""
        return self._context_sensitive_overrides

    def _create_l2r(self, values: Set[ValueType], context: Optional[ContextType]) -> Dict[ValueType, MatchTuple]:
        left_to_right: Dict[ValueType, MatchTuple]
        overrides: Dict[ValueType, CandidateType]  # Type on override check done during init

        if context is None:
            if self._context_sensitive_overrides:  # pragma: no cover
                raise TypeError("Must pass a context when using context-sensitive overrides.")
            overrides = self._overrides  # type: ignore
        else:
            if not self._context_sensitive_overrides:  # pragma: no cover
                raise TypeError("Overrides must be of type InheritedKeysDict when context is given.")
            overrides = self._overrides.get(context, {})  # type: ignore

        return {value: (overrides[value],) for value in filter(overrides.__contains__, values)}

    def _map_value(
        self, value: ValueType, candidates: Set[CandidateType], context: Optional[ContextType], kwargs: Dict[str, Any]
    ) -> Optional[MatchTuple]:
        scores = self._score(value, candidates, context, **self._score_kwargs, **kwargs)
        sorted_candidates = sorted(zip(scores, candidates), key=lambda t: -t[0])

        filtered_candidates = set(candidates)
        for filter_function, function_kwargs in self._filters:
            filtered_candidates = filter_function(value, filtered_candidates, context, **function_kwargs, **kwargs)

            not_in_original_candidates = filtered_candidates.difference(candidates)
            if not_in_original_candidates:
                raise exceptions.BadFilterError(
                    f"Filter {tname(filter_function)}({value}, candidates, **{kwargs}) created new"
                    f"candidates: {not_in_original_candidates}"
                )

            if not filtered_candidates:
                return None

        ans = []
        logger = LOGGER.getChild("reject")
        for score, candidate in sorted_candidates:
            if candidate not in filtered_candidates:
                score = -float("inf")

            if score >= self._min_score:
                ans.append(candidate)

                if LOGGER.isEnabledFor(logging.DEBUG):
                    cs = " (short-circuited)" if score == float("inf") else ""
                    extra = "" if self._cardinality == Cardinality.OneToOne else " Looking for more matches.."
                    LOGGER.debug(
                        f"Mapped: {repr(value)} -> {repr(candidate)}, {score=:2.3f} >= {self._min_score}{cs}.{extra}"
                    )

                if self._cardinality == Cardinality.OneToOne:
                    break
            elif logger.isEnabledFor(logging.DEBUG):
                extra = " (removed by filters)" if score == -float("inf") else ""
                logger.debug(f"Rejected: {repr(value)} -> {repr(candidate)}, {score=:.3f} < {self._min_score}{extra}.")

        return tuple(ans)

    def __repr__(self) -> str:
        score = self._score
        return f"{tname(self)}({score=} >= {self._min_score}, {len(self._filters)} filters)"

    def copy(self) -> "Mapper":
        """Make a copy of this Mapper."""
        return Mapper(
            score_function=self._score,
            score_function_kwargs=self._score_kwargs.copy(),
            filter_functions=[(func, kwargs.copy()) for func, kwargs in self._filters],
            min_score=self._min_score,
            overrides=self._overrides.copy(),
            unmapped_values_action=self._unmapped_action,
            cardinality=self._cardinality,
        )
