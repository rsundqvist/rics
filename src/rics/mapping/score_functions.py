"""Functions which return a likeness score."""
from typing import Callable, Collection, Hashable, Iterable, List, TypeVar, Union

H = TypeVar("H", bound=Hashable)
MappingScoreFunction = Callable[[H, Iterable[H]], Iterable[float]]
"""Signature for a likeness score function.

Args:
    name: An element to find matches for.
    candidates: Potential matches for `value`.

Keyword Args:
    kwargs: Accepted only by some functions.

Yields:
    A score for each candidate `c` in `candidates`.
"""


def modified_hamming(name: str, candidates: Iterable[str]) -> Iterable[float]:
    """Compute hamming distance modified by length ratio, from the back."""

    def _apply(candidate: str) -> float:
        sz = min(len(candidate), len(name))
        same = sum([name[i] == candidate[i] for i in range(-sz, 0)])

        ratio = 1 / (1 + abs(len(candidate) - len(name)))
        normalized_hamming = same / sz

        return ratio * normalized_hamming

    yield from map(_apply, candidates)


def equality(value: H, candidates: Iterable[H]) -> Iterable[float]:
    """Return 1.0 if ``k == c_i``, 0.0 otherwise.

    Args:
        value: An element to find matches for.
        candidates: Potential matches for `value`.

    Yields:
        A score for each candidate `c` in `candidates`.
    """
    yield from map(float, (value == c for c in candidates))


def like_database_table(
    name: str, candidates: Iterable[str], score_function: Union[str, MappingScoreFunction] = modified_hamming
) -> Iterable[float]:
    """Try to make `value` look like the name of a database table.

    Args:
        name: An element to find matches for.
        candidates: Potential matches for `value`.
        score_function: The actual scoring function to use after heuristics have been applied.

    Yields:
        A score for each candidate `c` in `candidates`.
    """
    fn: MappingScoreFunction = from_name(score_function) if isinstance(score_function, str) else score_function

    def apply(s: str) -> str:
        s = s.replace("_", "").replace(".", "")
        return s if s.endswith("s") else s + "s"

    if name.endswith("id"):
        name = name[: -len("id")]
    name = apply(name)

    yield from fn(name, map(apply, candidates))


def score_with_heuristics(
    value: str,  # placeholder
    candidates: Iterable[str],  # columns
    fstrings: Collection[str] = (),
    score_function: Union[str, MappingScoreFunction] = modified_hamming,
    source: str = None,
) -> Iterable[float]:
    """Return the best score per candidate when applying various heuristics before passing to `score_function`.

    Args:
        value: A placeholder to map to a column (=candidate).
        candidates: Potential matches for `value`.
        fstrings: Fstrings which take `value` and/or `source` placeholders.
        score_function: The actual scoring function to use after heuristics have been applied.
        source: A source (table) name.

    Yields:
        A score for each candidate `c` in `candidates`.
    """
    fn: MappingScoreFunction = from_name(score_function) if isinstance(score_function, str) else score_function

    with_heuristics = [value.lower()] + [fstr.format(value=value, source=source).lower() for fstr in fstrings]
    yield from (max(fn(column.lower(), with_heuristics)) for column in candidates)


def from_name(name: str) -> MappingScoreFunction:
    """Get a scoring function by name."""
    for func in _all_functions:
        if func.__name__ == name:
            return func

    raise ValueError(f"No score function called {repr(name)}.")


_all_functions: List[MappingScoreFunction] = [
    modified_hamming,
    like_database_table,
    equality,
    score_with_heuristics,
]
