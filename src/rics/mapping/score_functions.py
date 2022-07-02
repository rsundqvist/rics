"""Functions which return a likeness score."""
import logging
from typing import Callable, Hashable, Iterable, List, Optional, TypeVar, Union

LOGGER = logging.getLogger(__name__)

H = TypeVar("H", bound=Hashable)
ContextType = TypeVar("ContextType", bound=Hashable)
ScoreFunction = Callable[[H, Iterable[H], Optional[ContextType]], Iterable[float]]
"""Signature for a likeness score function.

Args:
    name: An element to find matches for.
    candidates: Potential matches for `value`.
    context: The context in which scoring is being performed.

Keyword Args:
    kwargs: Accepted only by some functions.

Yields:
    A score for each candidate `c` in `candidates`.
"""


def modified_hamming(name: str, candidates: Iterable[str], context: Optional[ContextType]) -> Iterable[float]:
    """Compute hamming distance modified by length ratio, from the back."""

    def _apply(candidate: str) -> float:
        sz = min(len(candidate), len(name))
        same = sum([name[i] == candidate[i] for i in range(-sz, 0)])

        ratio = 1 / (1 + abs(len(candidate) - len(name)))
        normalized_hamming = same / sz

        return ratio * normalized_hamming

    yield from map(_apply, candidates)


def equality(value: H, candidates: Iterable[H], context: Optional[ContextType]) -> Iterable[float]:
    """Return 1.0 if ``k == c_i``, 0.0 otherwise.

    Args:
        value: An element to find matches for.
        candidates: Potential matches for `value`.
        context: Context in which the function is being called.

    Yields:
        A score for each candidate `c` in `candidates`.
    """
    yield from map(float, (value == c for c in candidates))


def like_database_table(
    name: str,
    candidates: Iterable[str],
    context: Optional[str],
    score_function: Union[str, ScoreFunction] = modified_hamming,
) -> Iterable[float]:
    """Try to make `value` look like the name of a database table.

    Args:
        name: An element to find matches for.
        candidates: Potential matches for `value`.
        context: Context in which the function is being called.
        score_function: The actual scoring function to use after heuristics have been applied.

    Yields:
        A score for each candidate `c` in `candidates`.
    """
    fn: ScoreFunction = from_name(score_function) if isinstance(score_function, str) else score_function

    def apply(s: str) -> str:
        s = s.lower().replace("_", "").replace(".", "")
        s = s[: -len("id")] if s.endswith("id") else s
        s = s if s.endswith("s") else s + "s"
        return s

    yield from fn(apply(name), map(apply, candidates), context)


def from_name(name: str) -> ScoreFunction:
    """Get a scoring function by name."""
    for func in _all_functions:
        if func.__name__ == name:
            return func

    raise ValueError(f"No score function called {repr(name)}.")


_all_functions: List[ScoreFunction] = [
    modified_hamming,
    like_database_table,
    equality,
]
