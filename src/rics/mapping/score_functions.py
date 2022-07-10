"""Functions which return a likeness score."""
import logging
from typing import Iterable, Optional

from rics.mapping.types import CandidateType, ContextType, ValueType

LOGGER = logging.getLogger(__name__)


def modified_hamming(name: str, candidates: Iterable[str], context: Optional[ContextType]) -> Iterable[float]:
    """Compute hamming distance modified by length ratio, from the back.

    Examples:
        >>> from rics.mapping.score_functions import modified_hamming
        >>> print(list(modified_hamming('aa', ['aa', 'a', 'ab'], context=None)))
        [1.0, 0.5, 0.5]
        >>> print(list(modified_hamming('face', ['face', 'FAce', 'race', 'place'], context=None)))
        [1.0, 0.5, 0.75, 0.375]
    """

    def _apply(candidate: str) -> float:
        sz = min(len(candidate), len(name))
        same = sum([name[i] == candidate[i] for i in range(-sz, 0)])

        ratio = 1 / (1 + abs(len(candidate) - len(name)))
        normalized_hamming = same / sz

        return ratio * normalized_hamming

    yield from map(_apply, candidates)


def equality(value: ValueType, candidates: Iterable[CandidateType], context: Optional[ContextType]) -> Iterable[float]:
    """Return 1.0 if ``k == c_i``, 0.0 otherwise.

    Examples:
        >>> from rics.mapping.score_functions import equality
        >>> print(list(equality('a', 'aAb', context=None)))
        [1.0, 0.0, 0.0]
    """
    yield from map(float, (value == c for c in candidates))
