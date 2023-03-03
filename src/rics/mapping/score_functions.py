"""Functions which return a likeness score.

See Also:
    The :class:`~.HeuristicScore` class.
"""
from typing import Iterable, Optional

from .types import CandidateType, ContextType, ValueType

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
    positional_penalty: float = 0.001,
) -> Iterable[float]:
    """Compute hamming distance modified by length ratio, from the back. Score range is ``[0, 1]``.

    Keyword Args:
        add_length_ratio_term: If ``True``, score is divided by ``abs(len(name) - len(candidate))``.
        positional_penalty: A penalty applied to prefer earlier `candidates`, according to the formulare
            ``penalty = index(candidate) * positional_penalty)``.

    Examples:
        >>> from rics.mapping.score_functions import modified_hamming
        >>> print(list(modified_hamming('aa', ['aa', 'a', 'ab', 'aa'], context=None)))
        [1.0, 0.499, 0.498, 0.997]
        >>> print(list(modified_hamming('aa', ['aa', 'a', 'ab', 'aa'], context=None, positional_penalty=0)))
        [1.0, 0.5, 0.5, 1.0]
        >>> print(list(modified_hamming('face', ['face', 'FAce', 'race', 'place'], context=None)))
        [1.0, 0.499, 0.748, 0.372]
    """

    def _apply(candidate: str) -> float:
        sz = min(len(candidate), len(name))
        same = sum([name[i] == candidate[i] for i in range(-sz, 0)])

        ratio = (1 / (1 + abs(len(candidate) - len(name)))) if add_length_ratio_term else 1
        normalized_hamming = same / sz

        return ratio * normalized_hamming

    yield from (s - i * positional_penalty for i, s in enumerate(map(_apply, candidates)))


def equality(value: ValueType, candidates: Iterable[CandidateType], context: Optional[ContextType]) -> Iterable[float]:
    """Return 1.0 if ``k == c_i``, 0.0 otherwise.

    Examples:
        >>> from rics.mapping.score_functions import equality
        >>> print(list(equality('a', 'aAb', context=None)))
        [1.0, 0.0, 0.0]
    """
    yield from map(float, (value == c for c in candidates))


def disabled(value: ValueType, candidates: Iterable[CandidateType], context: Optional[ContextType]) -> Iterable[float]:
    """Special value to indicate that scoring logic has been disabled.

    This is a workaround to allow users to indicate that the scoring logic is disabled, and that overrides should be
    used instead. The ``disabled``-function has no special meaning to the mapper, and will be called as any other
    scoring function. This in turn will immediately raise a ``ScoringDisabledError``.

    Raises:
        ScoringDisabledError: Always.
    """
    from .exceptions import ScoringDisabledError

    raise ScoringDisabledError(value, candidates, context)
