"""Functions which return a likeness score."""
import logging
from typing import Callable, Hashable, Iterable, Optional, TypeVar

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
