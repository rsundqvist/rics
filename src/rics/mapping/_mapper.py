import logging
import warnings
from typing import Any, Dict, Generic, Iterable, List, Optional, Set, Tuple, Union

from rics.mapping import exceptions
from rics.mapping import filter_functions as mf
from rics.mapping import score_functions as sf
from rics.mapping._cardinality import Cardinality
from rics.mapping._directional_mapping import DirectionalMapping
from rics.mapping.exceptions import MappingError, MappingWarning, UserMappingError, UserMappingWarning
from rics.mapping.types import (
    CandidateType,
    ContextType,
    FilterFunction,
    MatchTuple,
    ScoreFunction,
    UserOverrideFunction,
    ValueType,
)
from rics.utility.action_level import ActionLevel, ActionLevelTypes
from rics.utility.collections.dicts import InheritedKeysDict
from rics.utility.misc import get_by_full_name, tname

LOGGER = logging.getLogger(__package__).getChild("Mapper")


class Mapper(Generic[ValueType, CandidateType, ContextType]):
    """Map values and candidates.

    Args:
        score_function: A callable which accepts a value `k` and an ordered collection of candidates `c`, returning a
            score ``s_i`` for each candidate `c_i` in `c`. Default: ``s_i = float(k == c_i)``. Higher=better match.
        score_function_kwargs: Keyword arguments for `score_function`.
        filter_functions: Function-kwargs pairs of filters to apply before scoring.
        min_score: Minimum score `s_i`, as given by ``score(k, c_i)``, to consider `k` a match for `c_i`.
        overrides: If a dict, assumed to be 1:1 mappings (`value` to `candidate`) which override the scoring logic. If
            :class:`.InheritedKeysDict`, the context passed to :meth:`apply` is used to retrieve specific overrides.
        unmapped_values_action: Action to take if mapping fails for any values.
        unknown_user_override_action: Action to take if a :attr:`~rics.mapping.types.UserOverrideFunction` returns an
            unknown candidate.
        cardinality: Desired cardinality for mapped values. Derive if ``None``.
    """

    def __init__(
        self,
        score_function: Union[str, ScoreFunction] = "equality",
        score_function_kwargs: Dict[str, Any] = None,
        filter_functions: Iterable[Tuple[Union[str, FilterFunction], Dict[str, Any]]] = (),
        min_score: float = 1.00,
        overrides: Union[InheritedKeysDict, Dict[ValueType, CandidateType]] = None,
        unmapped_values_action: ActionLevelTypes = "ignore",
        unknown_user_override_action: ActionLevelTypes = "raise",
        cardinality: Optional[Cardinality.ParseType] = Cardinality.ManyToOne,
    ) -> None:
        self._score = get_by_full_name(score_function, sf) if isinstance(score_function, str) else score_function
        self._score_kwargs = score_function_kwargs or {}
        self._min_score = min_score
        self._overrides: Union[InheritedKeysDict, Dict[ValueType, CandidateType]] = (
            overrides if isinstance(overrides, InheritedKeysDict) else (overrides or {})
        )
        self._context_sensitive_overrides = isinstance(self._overrides, InheritedKeysDict)
        self._unmapped_action: ActionLevel = ActionLevel.verify(unmapped_values_action)
        self._bad_candidate_action: ActionLevel = ActionLevel.verify(unknown_user_override_action)
        self._cardinality = None if cardinality is None else Cardinality.parse(cardinality, strict=True)
        self._filters: List[Tuple[FilterFunction, Dict[str, Any]]] = [
            ((get_by_full_name(func, mf) if isinstance(func, str) else func), kwargs)
            for func, kwargs in filter_functions
        ]

    def apply(
        self,
        values: Iterable[ValueType],
        candidates: Iterable[CandidateType],
        context: ContextType = None,
        override_function: UserOverrideFunction = None,
        **kwargs: Any,
    ) -> DirectionalMapping[ValueType, CandidateType]:
        """Map values to candidates.

        Args:
            values: Iterable of elements to match to candidates.
            candidates: Iterable of candidates to match with `value`. Duplicate elements will be discarded.
            context: Context in which mapping is being done.
            override_function: A callable that takes inputs (value, candidates, context) that returns either ``None``
                (let the regular mapping logic decide) or one of the candidates. Unlike static overrides, override
                functions may not return non-candidates as matches. How non-candidates returned by override functions is
                handled is determined by the :attr:`unknown_user_override_action` property.
            **kwargs: Runtime keyword arguments for score and filter functions. May be used to add information which is
                not known when the ``Mapper`` is initialized.

        Returns:
            A :class:`.DirectionalMapping` on the form ``{value: (matched_candidate,)}``. May be turned into a plain
            ``{value: candidate}`` dict by using the :meth:`.DirectionalMapping.flatten` function.

        Raises:
            MappingError: If any values failed to match and ``unmapped_values_action='raise'``.
            BadFilterError: If a filter returns candidates that are not a subset of the original candidates.
            UserMappingError: If `func` returns an unknown candidate.
        """
        candidates = set(candidates)
        values = set(values)
        left_to_right = self._create_l2r(values, context)

        if override_function:
            self._add_function_overrides(override_function, values, candidates, context, left_to_right)

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
                if self.unmapped_values_action is ActionLevel.RAISE:
                    LOGGER.error(msg)
                    raise MappingError(msg)
                elif self.unmapped_values_action is ActionLevel.WARN:
                    LOGGER.warning(msg)
                    warnings.warn(msg, MappingWarning)
                else:
                    LOGGER.debug(msg)

        return DirectionalMapping(
            cardinality=self._cardinality,
            left_to_right=left_to_right,
            _verify=True,
        )

    __call__ = apply

    @property
    def unmapped_values_action(self) -> ActionLevel:
        """Return the action to take if mapping fails for any values."""
        return self._unmapped_action

    @property
    def unknown_user_override_action(self) -> ActionLevel:
        """Return the action to take if an override function returns an unknown candidate."""
        return self._bad_candidate_action

    @property
    def context_sensitive_overrides(self) -> bool:
        """Return ``True`` if overrides are context sensitive."""
        return self._context_sensitive_overrides

    def _create_l2r(
        self,
        values: Set[ValueType],
        context: Optional[ContextType],
    ) -> Dict[ValueType, MatchTuple]:
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

    def _add_function_overrides(
        self,
        func: UserOverrideFunction,
        values: Iterable[ValueType],
        candidates: Set[CandidateType],
        context: Optional[ContextType],
        left_to_right: Dict[ValueType, MatchTuple],
    ) -> None:
        for value in values:
            user_override = func(value, candidates, context)
            if user_override is None:
                continue
            if user_override not in candidates:
                msg = (
                    f"The user-defined override function {func} returned an unknown "
                    f"candidate {repr(user_override)} for {value=}."
                )
                if self.unknown_user_override_action is ActionLevel.RAISE:
                    LOGGER.error(msg)
                    raise UserMappingError(msg, value, candidates)
                elif self.unknown_user_override_action is ActionLevel.WARN:
                    LOGGER.warning(msg)
                    warnings.warn(msg, UserMappingWarning)
                else:
                    LOGGER.debug(msg)
                continue

            LOGGER.debug(f"Using override {repr(value)} -> {repr(user_override)} returned by {func}.")
            left_to_right[value] = (user_override,)

    def _map_value(
        self,
        value: ValueType,
        candidates: Set[CandidateType],
        context: Optional[ContextType],
        kwargs: Dict[str, Any],
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
        """Make a copy of this ``Mapper``."""
        return Mapper(
            score_function=self._score,
            score_function_kwargs=self._score_kwargs.copy(),
            filter_functions=[(func, kwargs.copy()) for func, kwargs in self._filters],
            min_score=self._min_score,
            overrides=self._overrides.copy(),
            unmapped_values_action=self.unmapped_values_action,
            cardinality=self._cardinality,
        )
