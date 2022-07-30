"""Functions which return a likeness score.

See Also:
    The :class:`~rics.mapping.HeuristicScore` class.
"""
from typing import Iterable, Optional

from rics.mapping.types import CandidateType, ContextType, ValueType

VERBOSE: bool = False
"""If ``True`` enable optional DEBUG-level log messages on each score function invocation.

Notes:
    Not all functions have verbose messages.
"""


def modified_hamming(
    name: str,
    candidates: Iterable[str],
    context: Optional[ContextType],
    add_length_ratio_term: bool = True,
) -> Iterable[float]:
    """Compute hamming distance modified by length ratio, from the back. Score range is ``[0, 1]``.

    Keyword Args:
        add_length_ratio_term: If ``True``, score is divided by ``abs(len(name) - len(candidate))``.

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

        ratio = (1 / (1 + abs(len(candidate) - len(name)))) if add_length_ratio_term else 1
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
