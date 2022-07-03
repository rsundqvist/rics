import logging
from typing import Any, Dict, Generic, Hashable, Iterable, List, Optional, Tuple, TypeVar, Union

from rics.mapping import filter_functions, heuristic_functions
from rics.mapping import score_functions as sf
from rics.mapping.filter_functions import FilterFunction
from rics.mapping.heuristic_functions import AliasFunction
from rics.utility.misc import tname

LOGGER = logging.getLogger(__package__).getChild("HeuristicScore")

H = TypeVar("H", bound=Hashable)
ContextType = TypeVar("ContextType", bound=Hashable)
HeuristicsTypes = Union[AliasFunction, FilterFunction]
"""Heuristic function types."""


class HeuristicScore(Generic[H]):
    """Callable wrapper for computing heuristic scores.

    Instances are callable. Signature is given by :attr:`~rics.mapping.score_functions.ScoreFunction`.

    Short-circuiting:
        A mechanism for forced matching. Score is set to `+∞` for short-circuited candidates, and `-∞` for the rest.
        No further matching will be performed after this point, so ensure that all desired candidates are returned by
        chosen filters.

    Procedure:
        1. Trigger ``short-circuiting`` if there is an exact value-candidate match.
        2. All `heuristics` are applied and scores are computed.
        3. If no ``short-circuiting`` is triggered in step 2, yield max score for each candidate.

    Args:
        score_function: A :attr:`~rics.mapping.score_functions.ScoreFunction` to wrap.
        heuristics: Iterable of heuristics or tuples (heuristic, kwargs) to apply to the inputs of the score function.
            Applied in the order in which they are given.

    Heuristic types:
        * An :const:`~rics.mapping.heuristic_functions.AliasFunction`, which accepts and returns a tuple
          (value, candidates) to be evaluated.
        * A :const:`~rics.mapping.filter_functions.FilterFunction`, which accepts a tuple (value, candidates) and
          returns a subset of `candidates`. If any candidates are returned, ``short-circuiting`` is triggered.
    """

    def __init__(
        self,
        score_function: Union[str, sf.ScoreFunction],
        heuristics: Iterable[Union[Union[str, HeuristicsTypes], Tuple[Union[str, HeuristicsTypes], Dict[str, Any]]]],
    ) -> None:
        self._score: sf.ScoreFunction = (
            getattr(sf, score_function) if isinstance(score_function, str) else score_function
        )
        self._heuristics: List[Tuple[HeuristicsTypes, Dict[str, Any]]] = []

        for h in heuristics:
            func, kwargs = h if isinstance(h, tuple) else (h, {})
            self.add_heuristic(func, kwargs)

    def add_heuristic(self, heuristic: Union[str, HeuristicsTypes], kwargs: Dict[str, Any] = None) -> None:
        """Add a new heuristic."""
        new_heuristic = (_resolve_heuristic(heuristic), kwargs or {})
        self._heuristics.append(new_heuristic)

    def __repr__(self) -> str:
        score_function = self._score
        heuristics = self._heuristics
        return f"{tname(self)}({score_function=}, {heuristics=})"

    def __call__(
        self, value: H, candidates: Iterable[H], context: Optional[ContextType], **kwargs: Any
    ) -> Iterable[float]:
        """Apply `score_function` with heuristics and short-circuiting."""
        candidates = list(candidates)

        if value in candidates:
            yield from (float("inf") if c == value else -float("inf") for c in candidates)

        best = list(self._score(value, candidates, context, **kwargs))

        for func, func_kwargs in self._heuristics:
            res = func(value, candidates, context, **func_kwargs)
            if isinstance(res, tuple):  # Alias function -- res is a modified (value, candidates) tuple
                for i, score in enumerate(self._score(*res, context, **kwargs)):
                    best[i] = max(best[i], score)
            else:  # Filter function
                if res:
                    LOGGER.debug(f"Short circuit {value=} -> candidates={repr(res)} triggered by {tname(func)}.")
                    yield from (float("inf") if c in res else -float("inf") for c in candidates)
                    return  # Short-circuit
        yield from best

    def __str__(self) -> str:
        chain = " | ".join(tname(f) for f, kwargs in self._heuristics)
        return f"{tname(self)}([{chain}] -> {tname(self._score)})"


def _resolve_heuristic(func_or_name: Union[str, HeuristicsTypes]) -> HeuristicsTypes:  # pragma: no cover
    if isinstance(func_or_name, str):
        try:
            return getattr(filter_functions, func_or_name)
        except AttributeError:
            pass
        try:
            return getattr(heuristic_functions, func_or_name)
        except AttributeError:
            pass

        raise KeyError(func_or_name)
    else:
        return func_or_name
