import logging
from typing import Any, Dict, Generic, Iterable, List, Optional, Tuple, Union

from rics.mapping import filter_functions, heuristic_functions, score_functions
from rics.mapping.types import CandidateType, ContextType, HeuristicsTypes, ScoreFunction, ValueType
from rics.utility.misc import get_by_full_name, tname

LOGGER = logging.getLogger(__package__).getChild("HeuristicScore")


class HeuristicScore(Generic[ValueType, CandidateType, ContextType]):
    """Callable wrapper for computing heuristic scores.

    Instances are callable. Signature is given by :attr:`~rics.mapping.types.ScoreFunction`.

    Short-circuiting:
        A mechanism for forced matching. Score is set to `+∞` for short-circuited candidates, and `-∞` for the rest.
        No further matching will be performed after this point, so ensure that all desired candidates are returned by
        chosen filters.

    Procedure:
        1. Trigger ``short-circuiting`` if there is an exact value-candidate match.
        2. All `heuristics` are applied and scores are computed.
        3. If no ``short-circuiting`` is triggered in step 2, yield max score for each candidate.

    Args:
        score_function: A :attr:`~rics.mapping.types.ScoreFunction` to wrap.
        heuristics: Iterable of heuristics or tuples (heuristic, kwargs) to apply to the (value, candidates) inputs to
            the `score_function`.

    Heuristic types:
        * An :const:`~rics.mapping.types.AliasFunction`, which accepts and returns a tuple
          (value, candidates) to be evaluated.
        * A :const:`~rics.mapping.types.FilterFunction`, which accepts a tuple (value, candidates) and
          returns a subset of `candidates`. If any candidates are returned, ``short-circuiting`` is triggered.

    Notes:
        * Heuristic function input order = application order.
        * You may add ``mutate=True`` to the heuristics kwargs to forward to the modifications made by that function.
    """

    def __init__(
        self,
        score_function: Union[str, ScoreFunction],
        heuristics: Iterable[Union[Union[str, HeuristicsTypes], Tuple[Union[str, HeuristicsTypes], Dict[str, Any]]]],
    ) -> None:
        self._score: ScoreFunction = (
            get_by_full_name(score_function, score_functions) if isinstance(score_function, str) else score_function
        )
        self._heuristics: List[Tuple[HeuristicsTypes, Dict[str, Any]]] = []

        for h in heuristics:
            func, kwargs = h if isinstance(h, tuple) else (h, {})
            self.add_heuristic(func, kwargs)

    @property
    def score_function(self) -> ScoreFunction:
        """Return the underlying likeness score function."""
        return self._score

    def add_heuristic(self, heuristic: Union[str, HeuristicsTypes], kwargs: Dict[str, Any] = None) -> None:
        """Add a new heuristic."""
        new_heuristic = (_resolve_heuristic(heuristic), kwargs or {})
        self._heuristics.append(new_heuristic)

    def __repr__(self) -> str:
        score_function = self._score
        heuristics = self._heuristics
        return f"{tname(self)}({score_function=}, {heuristics=})"

    def __call__(
        self, value: ValueType, candidates: Iterable[CandidateType], context: Optional[ContextType], **kwargs: Any
    ) -> Iterable[float]:
        """Apply `score_function` with heuristics and short-circuiting."""
        candidates = list(candidates)

        if value in candidates:
            yield from (float("inf") if c == value else -float("inf") for c in candidates)

        base_score = list(self._score(value, candidates, context, **kwargs))  # Unmodified score
        best = list(base_score)

        h_value = value
        h_candidates = list(candidates)
        for func, func_kwargs in self._heuristics:
            func_kwargs = func_kwargs.copy()
            mutate = func_kwargs.pop("mutate", False)
            res = func(h_value, h_candidates, context, **func_kwargs)
            if isinstance(res, tuple):  # Alias function -- res is a modified (value, candidates) tuple
                res_value, res_candidates = res[0], list(res[1])
                for i, heuristic_score in enumerate(self._score(res_value, res_candidates, context, **kwargs)):
                    best[i] = max(best[i], heuristic_score)
                if mutate:
                    h_value, h_candidates = res_value, res_candidates
            else:  # Filter function
                if mutate:  # pragma: no cover
                    LOGGER.warning(f"Ignoring {mutate=} for filter function {func=}.")

                if res:
                    if heuristic_functions.VERBOSE and LOGGER.isEnabledFor(logging.DEBUG):
                        base_args = ", ".join([repr(h_value), repr(h_candidates), f"{context=}"])
                        extra_args = ", ".join(f"{k}={repr(v)}" for k, v, in func_kwargs.items())
                        info = f"{tname(func)}({', '.join([base_args, extra_args])})"
                        LOGGER.debug(f"Short-circuit {value=} -> candidates={repr(res)}, triggered by {info}.")
                    yield from (float("inf") if c in res else -float("inf") for c in h_candidates)
                    return  # Short-circuit

        if heuristic_functions.VERBOSE and LOGGER.isEnabledFor(logging.DEBUG):
            changes = [
                f"{repr(cand)}: {score:.2f} -> {heuristic_score:.2f} ({heuristic_score-score:+.2f})"
                for cand, score, heuristic_score in zip(candidates, base_score, best)
            ]
            LOGGER.debug(f"Heuristics scores for {value=}: [{', '.join(changes)}]")

        yield from best

    def __str__(self) -> str:
        chain = " | ".join(tname(f) for f, kwargs in self._heuristics)
        return f"{tname(self)}([{chain}] -> {tname(self.score_function)})"


def _resolve_heuristic(func_or_name: Union[str, HeuristicsTypes]) -> HeuristicsTypes:  # pragma: no cover
    if isinstance(func_or_name, str):
        try:
            return get_by_full_name(func_or_name, filter_functions)
        except AttributeError:
            pass
        try:
            return get_by_full_name(func_or_name, heuristic_functions)
        except AttributeError:
            pass

        raise KeyError(func_or_name)
    else:
        return func_or_name
