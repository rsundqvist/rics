import logging
import warnings
from time import perf_counter
from typing import Any, Dict, Generic, Iterable, List, Optional, Set, Tuple, Union

import numpy as np
import pandas as pd

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
    ScoreFunction,
    UserOverrideFunction,
    ValueType,
)
from rics.performance import format_perf_counter
from rics.utility.action_level import ActionLevel
from rics.utility.collections.dicts import InheritedKeysDict
from rics.utility.misc import get_by_full_name, tname

LOGGER = logging.getLogger(__package__).getChild("Mapper")


class Mapper(Generic[ValueType, CandidateType, ContextType]):
    """Optimal value-candidate matching.

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
        cardinality: Desired cardinality for mapped values. Disable checks if ``None``. Otherwise, raise an error if the
            actual cardinality computed for a matching is greater than the desired cardinality (ie the ``Mapper`` made
            too many matches).
        enable_verbose_logging: If ``True``, enable verbose logging for the :meth:`apply` function. Has no effect when
            the log level is above ``logging.DEBUG``.

    See Also:
        The :ref:`mapping-primer` page.
    """

    def __init__(
        self,
        score_function: Union[str, ScoreFunction] = "equality",
        score_function_kwargs: Dict[str, Any] = None,
        filter_functions: Iterable[Tuple[Union[str, FilterFunction], Dict[str, Any]]] = (),
        min_score: float = 1.00,
        overrides: Union[InheritedKeysDict, Dict[ValueType, CandidateType]] = None,
        unmapped_values_action: ActionLevel.ParseType = ActionLevel.IGNORE,
        unknown_user_override_action: ActionLevel.ParseType = ActionLevel.RAISE,
        cardinality: Optional[Cardinality.ParseType] = Cardinality.ManyToOne,
        enable_verbose_logging: bool = False,
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
        self._verbose = enable_verbose_logging

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
            override_function: A callable that takes inputs ``(value, candidates, context)`` that returns either
                ``None`` (let the regular mapping logic decide) or one of the `candidates`. Unlike static overrides,
                override functions may not return non-candidates as matches. How non-candidates returned by override
                functions is handled is determined by the :attr:`unknown_user_override_action` property.
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
        if self.verbose:  # pragma: no cover
            from rics.mapping.support import enable_verbose_debug_messages

            with enable_verbose_debug_messages():
                scores = self.compute_scores(values, candidates, context, override_function, **kwargs)
        else:
            scores = self.compute_scores(values, candidates, context, override_function, **kwargs)

        start = perf_counter()
        dm: DirectionalMapping[ValueType, CandidateType] = self.to_directional_mapping(scores)

        unmapped = set(scores.index[~np.isinf(scores).all(axis=1)]).difference(dm.left)
        if unmapped:
            extra = f" in {context=}" if context else ""
            candidates = set(scores)
            self._report_unmapped(f"Could not map {unmapped}{extra} to any of {candidates=}.")

        if LOGGER.isEnabledFor(logging.DEBUG):
            cardinality = "automatic" if self.cardinality is None else self.cardinality.name
            LOGGER.debug(f"Match selection with {cardinality=} completed in {format_perf_counter(start)}.")

        return dm

    def _report_unmapped(self, msg: str) -> None:  # pragma: no cover
        logger = LOGGER.getChild("unmapped")
        if self.unmapped_values_action is ActionLevel.RAISE:
            logger.error(msg)
            raise MappingError(msg)
        elif self.unmapped_values_action is ActionLevel.WARN:
            logger.warning(msg)
            warnings.warn(msg, MappingWarning)
        else:
            logger.debug(msg)

    def compute_scores(
        self,
        values: Iterable[ValueType],
        candidates: Iterable[CandidateType],
        context: ContextType = None,
        override_function: UserOverrideFunction = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """Compute likeness scores.

        Args:
            values: Iterable of elements to match to candidates.
            candidates: Iterable of candidates to match with `value`. Duplicate elements will be discarded.
            context: Context in which mapping is being done.
            override_function: A callable that takes inputs ``(value, candidates, context)`` that returns either
                ``None`` (let the regular mapping logic decide) or one of the `candidates`. Unlike static overrides,
                override functions may not return non-candidates as matches. How non-candidates returned by override
                functions is handled is determined by the :attr:`unknown_user_override_action` property.
            **kwargs: Runtime keyword arguments for score and filter functions. May be used to add information which is
                not known when the ``Mapper`` is initialized.

        Returns:
            A ``DataFrame`` of value-candidate match scores, with ``DataFrame.index=values`` and
            ``DataFrame.columns=candidates``.
        """
        start = perf_counter()

        scores = pd.DataFrame(
            data=-np.inf,
            columns=pd.Index(set(candidates), name="candidates"),
            index=pd.Index(set(values), name="values"),
            dtype=float,
        )

        unmapped_values = set(scores.index)
        for value, override_candidate in self._get_static_overrides(scores.index, context):
            scores.loc[value, override_candidate] = np.inf
            unmapped_values.discard(value)

        if override_function:
            for value, override_candidate in self._get_function_overrides(
                override_function, scores.index, scores.columns, context
            ):
                LOGGER.debug(
                    f"Using override {repr(value)} -> {repr(override_candidate)} returned by {override_function}."
                )
                if override_candidate in scores:
                    scores.loc[value, override_candidate] = np.inf
                    unmapped_values.discard(value)

        extra = f" in {context=}" if context else ""
        for value in unmapped_values:
            if LOGGER.isEnabledFor(logging.DEBUG):
                candidates = set(scores.columns)
                LOGGER.debug(f"Begin computing match scores for {value=}{extra} to {candidates=} using {self._score}.")

            filtered_candidates = self._apply_filters(value, scores.columns, context, kwargs)
            scores_for_value = self._score(value, filtered_candidates, context, **self._score_kwargs, **kwargs)
            for score, candidate in zip(scores_for_value, filtered_candidates):
                scores.loc[value, candidate] = score

        if LOGGER.isEnabledFor(logging.DEBUG):
            LOGGER.debug(f"Computed {scores.size} match scores in {format_perf_counter(start)}:\n{scores.to_string()}")
        return scores

    def to_directional_mapping(
        self,
        scores: pd.DataFrame,
    ) -> DirectionalMapping[ValueType, CandidateType]:
        """Create a ``DirectionalMapping`` from match scores.

        Args:
            scores: A score matrix, where ``scores.index`` are values and ``score.columns`` are treated as the
                candidates.

        Returns:
            A ``DirectionalMapping``.

        See Also:
            :meth:`.MatchScores.to_directional_mapping`
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            from rics.mapping.support import MatchScores
        return MatchScores(scores, self._min_score).to_directional_mapping(self.cardinality)

    @property
    def cardinality(self) -> Optional[Cardinality]:
        """Return upper cardinality bound during mapping."""
        return self._cardinality

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

    @property
    def verbose(self) -> bool:
        """Return ``True`` if verbose debug-level messages are enabled."""
        return self._verbose

    def _get_static_overrides(
        self,
        values: Iterable[ValueType],
        context: Optional[ContextType],
    ) -> List[Tuple[ValueType, CandidateType]]:
        overrides: Dict[ValueType, CandidateType]  # Type on override check done during init

        if context is None:
            if self._context_sensitive_overrides:  # pragma: no cover
                raise TypeError("Must pass a context when using context-sensitive overrides.")
            overrides = self._overrides  # type: ignore
        else:
            if not self._context_sensitive_overrides:  # pragma: no cover
                raise TypeError("Overrides must be of type InheritedKeysDict when context is given.")
            overrides = self._overrides.get(context, {})  # type: ignore

        return [(value, overrides[value]) for value in filter(overrides.__contains__, values)]

    def _get_function_overrides(
        self,
        func: UserOverrideFunction,
        values: Iterable[ValueType],
        candidates: Iterable[CandidateType],
        context: Optional[ContextType],
    ) -> List[Tuple[ValueType, CandidateType]]:
        candidates = set(candidates)

        ans = []
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

            ans.append((value, user_override))

        return ans

    def _apply_filters(
        self,
        value: ValueType,
        candidates: Iterable[CandidateType],
        context: Optional[ContextType],
        kwargs: Dict[str, Any],
    ) -> Set[CandidateType]:
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
                break

        return filtered_candidates

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
            cardinality=self.cardinality,
        )
