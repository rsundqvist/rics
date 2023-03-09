import logging
import warnings
from time import perf_counter
from typing import Any, Dict, Generic, Iterable, List, Optional, Set, Tuple, Union

import numpy as np
import pandas as pd

from rics.mapping import exceptions, filter_functions as mf, score_functions as sf
from rics.performance import format_perf_counter

from ..action_level import ActionLevel
from ..collections.dicts import InheritedKeysDict
from ..misc import get_by_full_name, tname
from ._cardinality import Cardinality
from ._directional_mapping import DirectionalMapping
from .exceptions import MappingError, MappingWarning, UserMappingError, UserMappingWarning
from .types import CandidateType, ContextType, FilterFunction, ScoreFunction, UserOverrideFunction, ValueType

with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=UserWarning)
    from .support import MatchScores, enable_verbose_debug_messages

LOGGER = logging.getLogger(__package__).getChild("Mapper")


class Mapper(Generic[ValueType, CandidateType, ContextType]):
    """Optimal value-candidate matching.

    For an introduction to mapping, see the :ref:`mapping-primer` page.

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
            unknown candidate. Unknown candidates, i.e. candidates not in the input `candidates` collection, will not be
            used unless `'ignore'` is chosen. As such, `'ignore'` should rather be interpreted as `'allow'`.
        cardinality: Desired cardinality for mapped values. Derive for each matching if ``None``.
        verbose_logging: If ``True``, enable verbose logging for the :meth:`apply` function. Has no effect when the log
            level is above ``logging.DEBUG``.
    """

    def __init__(
        self,
        score_function: Union[str, ScoreFunction[ValueType, CandidateType, ContextType]] = "equality",
        score_function_kwargs: Dict[str, Any] = None,
        filter_functions: Iterable[
            Tuple[Union[str, FilterFunction[ValueType, CandidateType, ContextType]], Dict[str, Any]]
        ] = (),
        min_score: float = 0.90,
        overrides: Union[
            InheritedKeysDict[ContextType, ValueType, CandidateType], Dict[ValueType, CandidateType]
        ] = None,
        unmapped_values_action: ActionLevel.ParseType = ActionLevel.IGNORE,
        unknown_user_override_action: ActionLevel.ParseType = ActionLevel.RAISE,
        cardinality: Optional[Cardinality.ParseType] = Cardinality.ManyToOne,
        verbose_logging: bool = False,
    ) -> None:
        self._score = get_by_full_name(score_function, sf) if isinstance(score_function, str) else score_function
        self._score_kwargs = score_function_kwargs or {}
        self._min_score = min_score
        self._overrides: Union[
            InheritedKeysDict[ContextType, ValueType, CandidateType], Dict[ValueType, CandidateType]
        ] = (overrides if isinstance(overrides, InheritedKeysDict) else (overrides or {}))
        self._unmapped_action: ActionLevel = ActionLevel.verify(unmapped_values_action)
        self._bad_candidate_action: ActionLevel = ActionLevel.verify(unknown_user_override_action)
        self._cardinality = None if cardinality is None else Cardinality.parse(cardinality, strict=True)
        self._filters: List[Tuple[FilterFunction[ValueType, CandidateType, ContextType], Dict[str, Any]]] = [
            ((get_by_full_name(func, mf) if isinstance(func, str) else func), kwargs)
            for func, kwargs in filter_functions
        ]
        self._verbose = verbose_logging

    def apply(
        self,
        values: Iterable[ValueType],
        candidates: Iterable[CandidateType],
        context: ContextType = None,
        override_function: UserOverrideFunction[ValueType, CandidateType, ContextType] = None,
        **kwargs: Any,
    ) -> DirectionalMapping[ValueType, CandidateType]:
        """Map values to candidates.

        Args:
            values: Iterable of elements to match to candidates.
            candidates: Iterable of candidates to match with `value`. Duplicate elements will be discarded.
            context: Context in which mapping is being done. Required when using context-sensitive overrides.
            override_function: A callable that takes inputs ``(value, candidates, context)`` that returns either
                ``None`` (let the regular mapping logic decide) or one of the `candidates`. How non-candidates returned
                is handled is determined by the :attr:`unknown_user_override_action` property.
            **kwargs: Runtime keyword arguments for score and filter functions. May be used to add information which is
                not known when the ``Mapper`` is initialized.

        Returns:
            A :class:`.DirectionalMapping` on the form ``{value: [matched_candidates, ...]}``. May be turned into a
            plain dict ``{value: candidate}`` by using the :meth:`.DirectionalMapping.flatten` function (only if
            :attr:`.DirectionalMapping.cardinality` is of type :attr:`.Cardinality.one_right`).

        Raises:
            MappingError: If any values failed to match and ``unmapped_values_action='raise'``.
            BadFilterError: If a filter returns candidates that are not a subset of the original candidates.
            UserMappingError: If `override_function` returns an unknown candidate and
                ``unknown_user_override_action != 'ignore'``
            ValueError: If passing ``context=None`` (the default) when  :attr:`context_sensitive_overrides` is ``True``.
        """
        start = perf_counter()

        if isinstance(self._overrides, InheritedKeysDict) and context is None:
            raise ValueError("Must pass a context in context-sensitive mode.")

        if self.verbose_logging:
            with enable_verbose_debug_messages():
                scores = self.compute_scores(values, candidates, context, override_function, **kwargs)
        else:
            scores = self.compute_scores(values, candidates, context, override_function, **kwargs)  # pragma: no cover

        dm: DirectionalMapping[ValueType, CandidateType] = self.to_directional_mapping(scores)

        unmapped = set(scores.index[~np.isinf(scores).all(axis=1)]).difference(dm.left)
        if unmapped:
            extra = f" in {context=}" if context else ""
            candidates = set(scores)
            self._report_unmapped(f"Could not map {unmapped}{extra} to any of {candidates=}.")

        if LOGGER.isEnabledFor(logging.DEBUG):
            values = list(scores.index)
            candidates = list(scores.columns)
            cardinality = "automatic" if self.cardinality is None else self.cardinality.name

            l2r = dm.left_to_right
            matches = " Matches:\n" + "\n".join(
                (f"    {v!r} -> {repr(l2r[v]) if v in l2r else '<no match>'}" for v in values)
            )

            LOGGER.debug(
                f"Mapping with {cardinality=} completed for {values}x{candidates} in {format_perf_counter(start)}."
                f"{matches}\nMatched {len(dm.left)}/{len(values)} values with {len(dm.right)} different candidates."
            )

        return dm

    def _report_unmapped(self, msg: str) -> None:
        logger = LOGGER.getChild("unmapped")
        if self.unmapped_values_action is ActionLevel.RAISE:
            msg += (
                "\nHint: set "
                f"unmapped_values_action='{ActionLevel.WARN.value}' or "
                f"unmapped_values_action='{ActionLevel.IGNORE.value}' "
                "to allow unmapped values."
            )
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
        override_function: UserOverrideFunction[ValueType, CandidateType, ContextType] = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """Compute likeness scores.

        Args:
            values: Iterable of elements to match to candidates.
            candidates: Iterable of candidates to match with `value`. Duplicate elements will be discarded.
            context: Context in which mapping is being done.
            override_function: A callable that takes inputs ``(value, candidates, context)`` that returns either
                ``None`` (let the regular mapping logic decide) or one of the `candidates`. How non-candidates returned
                is handled is determined by the :attr:`unknown_user_override_action` property.
            **kwargs: Runtime keyword arguments for score and filter functions. May be used to add information which is
                not known when the ``Mapper`` is initialized.

        Returns:
            A ``DataFrame`` of value-candidate match scores, with ``DataFrame.index=values`` and
            ``DataFrame.columns=candidates``.

        Raises:
            BadFilterError: If a filter returns candidates that are not a subset of the original candidates.
            UserMappingError: If `override_function` returns an unknown candidate and
                ``unknown_user_override_action != 'ignore'``
        """
        start = perf_counter()

        scores = pd.DataFrame(
            data=-np.inf,
            columns=pd.Index(list(candidates), name="candidates").drop_duplicates(),
            index=pd.Index(list(values), name="values").drop_duplicates(),
            dtype=float,
        )

        extra = f" in {context=}" if context else ""

        if scores.empty:
            if LOGGER.isEnabledFor(logging.DEBUG):
                candidates = list(scores.columns)
                values = list(scores.index)
                end = "" if values or candidates else ", but got neither"
                LOGGER.debug(
                    f"Abort mapping{extra} of {values}x{candidates}. Both values and candidates must be given{end}."
                )
            return scores

        if LOGGER.isEnabledFor(logging.DEBUG):
            candidates = list(scores.columns)
            values = list(scores.index)
            LOGGER.debug(f"Begin computing match scores{extra} for {values}x{candidates} using {self._score}.")

        unmapped_values = self._handle_overrides(scores, context, override_function)
        if not unmapped_values:
            return scores

        for value in unmapped_values:
            filtered_candidates = self._apply_filters(value, scores.columns, context, kwargs)
            if not filtered_candidates:
                continue

            if self.verbose_logging and LOGGER.isEnabledFor(logging.DEBUG):
                LOGGER.debug(f"Compute match scores for {value=}.")
            scores_for_value = self._score(value, filtered_candidates, context, **self._score_kwargs, **kwargs)
            for score, candidate in zip(scores_for_value, filtered_candidates):
                scores.loc[value, candidate] = score

        if LOGGER.isEnabledFor(logging.DEBUG):
            LOGGER.debug(
                f"Computed {len(scores.index)}x{len(scores.columns)} "
                f"match scores in {format_perf_counter(start)}:\n{scores.to_string()}"
            )
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
        """Return the action to take if an override function returns an unknown candidate.

        Unknown candidates, i.e. candidates not in the input `candidates` collection, will not be used unless `'ignore'`
        is chosen. As such, `'ignore'` should rather be interpreted as `'allow'`.

        Returns:
            Action to take if a user-defined override function returns an unknown candidate.
        """
        return self._bad_candidate_action

    @property
    def context_sensitive_overrides(self) -> bool:
        """Return ``True`` if the overrides are context-sensitive."""
        return isinstance(self._overrides, InheritedKeysDict)

    @property
    def verbose_logging(self) -> bool:
        """Return ``True`` if verbose debug-level messages are enabled."""
        return self._verbose

    def _handle_overrides(
        self,
        scores: pd.DataFrame,
        context: Optional[ContextType],
        override_function: Optional[UserOverrideFunction[ValueType, CandidateType, ContextType]],
    ) -> List[ValueType]:
        applied: Dict[ValueType, CandidateType] = {}

        def apply(v: ValueType, oc: CandidateType) -> None:
            scores.loc[v, :] = -np.inf
            scores.loc[v, oc] = np.inf
            unmapped_values.remove(v)
            applied[v] = oc

        unmapped_values = list(scores.index)

        if override_function:
            for value, override_candidate in self._get_function_overrides(
                override_function, scores.index, scores.columns, context
            ):
                if LOGGER.isEnabledFor(logging.DEBUG):
                    LOGGER.debug(
                        f"Using override {repr(value)} -> {repr(override_candidate)} returned by {override_function}."
                    )
                apply(value, override_candidate)

        for value, override_candidate in self._get_static_overrides(unmapped_values, context):
            apply(value, override_candidate)

        if LOGGER.isEnabledFor(logging.DEBUG) and (self._overrides or override_function is not None):
            num_overrides = len(self._overrides) + int(override_function is not None)
            result = f"and found {len(applied)} matches={applied} in" if applied else "but none were a match for"
            done = "All values mapped by overrides. " if (not unmapped_values and applied) else ""
            LOGGER.debug(f"{done}Applied {num_overrides} overrides, {result} the given values={list(scores.index)}.")

        return unmapped_values

    def _get_static_overrides(
        self,
        values: Iterable[ValueType],
        context: Optional[ContextType],
    ) -> List[Tuple[ValueType, CandidateType]]:
        if not self._overrides:
            return []

        # The assertions are redundant (checked earlier), but makes mypy happy without type-ignores.
        if self.context_sensitive_overrides:
            assert isinstance(self._overrides, InheritedKeysDict), "Makes mypy happy."  # noqa: S101
            assert context is not None, "Makes mypy happy."  # noqa: S101
            overrides = self._overrides.get(context, {})
        else:
            assert not isinstance(self._overrides, InheritedKeysDict), "Makes mypy happy."  # noqa: S101
            assert context is None, "Makes mypy happy."  # noqa: S101
            overrides = self._overrides

        return [(value, overrides[value]) for value in filter(overrides.__contains__, values)]

    def _get_function_overrides(
        self,
        func: UserOverrideFunction[ValueType, CandidateType, ContextType],
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
            if self.unknown_user_override_action is not ActionLevel.IGNORE and user_override not in candidates:
                msg = (
                    f"The user-defined override function {func} returned an unknown candidate={repr(user_override)} for"
                    f" {value=}. If this is intended behaviour, set unknown_user_override_action='ignore' to allow."
                )
                if self.unknown_user_override_action is ActionLevel.RAISE:
                    LOGGER.error(msg)
                    raise UserMappingError(msg, value, candidates)
                elif self.unknown_user_override_action is ActionLevel.WARN:
                    msg += " The override has been ignored."
                    LOGGER.warning(msg)
                    warnings.warn(msg, UserMappingWarning)
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
        candidates = list(candidates)
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

        if self.verbose_logging and LOGGER.isEnabledFor(logging.DEBUG) and len(self._filters):
            diff = set(candidates).difference(filtered_candidates)
            removed = f"removing candidates={diff}" if diff else "but did not remove any candidates"
            done = "All candidates removed by filtering. " if not filtered_candidates else ""
            LOGGER.debug(f"{done}Applied {len(self._filters)} filters for {value=}, {removed}.")

        return filtered_candidates

    def __repr__(self) -> str:
        score = self._score
        return f"{tname(self)}({score=} >= {self._min_score}, {len(self._filters)} filters)"

    def copy(self, **overrides: Any) -> "Mapper[ValueType, CandidateType, ContextType]":
        """Make a copy of this ``Mapper``.

        Args:
            overrides: Keyword arguments to use when instantiating the copy. Options that aren't given will be taken
                from the current instance. See the :class:`Mapper` class documentation for possible choices.

        Returns:
            A copy of this ``Mapper`` with `overrides` applied.
        """
        kwargs: Dict[str, Any] = {
            "score_function": self._score,
            "min_score": self._min_score,
            "unmapped_values_action": self.unmapped_values_action,
            "unknown_user_override_action": self.unknown_user_override_action,
            "cardinality": self.cardinality,
            "verbose_logging": self.verbose_logging,
            **overrides,
        }

        if "score_function_kwargs" not in kwargs:
            kwargs["score_function_kwargs"] = self._score_kwargs.copy()

        if "filter_functions" not in kwargs:
            kwargs["filter_functions"] = [(func, func_kwargs.copy()) for func, func_kwargs in self._filters]

        if "overrides" not in kwargs:
            kwargs["overrides"] = self._overrides.copy()

        return Mapper(**kwargs)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Mapper):
            return False

        return all(
            (
                self._score == other._score,
                self._score_kwargs == other._score_kwargs,
                self._filters == other._filters,
                self._min_score == other._min_score,
                self._overrides == other._overrides,
                self._unmapped_action == other._unmapped_action,
                self._bad_candidate_action == other._bad_candidate_action,
                self._cardinality == other._cardinality,
                self._verbose == other._verbose,
            )
        )
