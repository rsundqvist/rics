import logging
from typing import Any, Dict, Generic, Hashable, Iterable, List, Optional, Tuple, TypeVar, Union

from rics.mapping import filter_functions, heuristic_functions
from rics.mapping.filter_functions import FilterFunction
from rics.mapping.heuristic_functions import AliasFunction
from rics.mapping.score_functions import ScoreFunction, from_name
from rics.utility.misc import tname

LOGGER = logging.getLogger(__name__)

H = TypeVar("H", bound=Hashable)
ContextType = TypeVar("ContextType", bound=Hashable)
HeuristicsTypes = Union[AliasFunction, FilterFunction]


class HeuristicScore(Generic[H]):
    """Callable wrapper for computing heuristic scores.

    Instances are callable. Signature is given by :const:`~rics.mapping.score_functions.ScoreFunction`.

    Procedure:
        1. Exact matches are always preferred, and will trigger ``short-circuiting`` for the matching candidate.
        2. All `heuristics` are applied and scores are computed.
        3. If no ``short-circuiting`` was triggered by filter functions, yield the highest score for each candidate.

    Heuristics may be of two kinds:
        * An :const:`AliasFunction`, which accepts and returns a tuple (value, candidates) to be evaluated.
        * A :const:`FilterFunction`, which accepts a tuple (value, candidates) and returns a subset of `candidates`. If
          any candidates are returned, ``short-circuiting`` is triggered.

    Args:
        score_function: An underlying score function.
        heuristics: Tuples (HeuristicType, kwargs) to apply to the inputs of the score function. Keyword arguments will
            be reused between calls. Applied in the given order, so filters that are likely to trigger should be placed
            early.

    Raises:
        ValueError: If no `heuristics` are given.
        KeyError: If a given function name cannot be found.

    Notes:
        ``Short-circuiting`` is a mechanism for forced matching. The score for short-circuited candidates are set to
        `+∞` and `-∞` for the rest. No further matching will be performed after this point, so take care that any
        filter functions you use return all desired candidates.
    """

    LOGGER = logging.getLogger(__package__).getChild("HeuristicScore")

    def __init__(
        self,
        score_function: Union[str, ScoreFunction],
        heuristics: Iterable[Tuple[Union[str, HeuristicsTypes], Dict[str, Any]]],
    ) -> None:
        if not heuristics:  # pragma: no cover
            raise ValueError("No heuristics given.")

        self._score: ScoreFunction = from_name(score_function) if isinstance(score_function, str) else score_function

        self._heuristics: List[Tuple[HeuristicsTypes, Dict[str, Any]]] = [
            (_resolve_heuristic(func_or_name), func_kwargs) for func_or_name, func_kwargs in heuristics
        ]

    def add_heuristic(self, heuristic: Union[str, HeuristicsTypes], kwargs: Dict[str, Any]) -> None:
        """Add a new heuristic."""
        new_heuristic = (_resolve_heuristic(heuristic), kwargs)
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
