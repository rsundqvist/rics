"""Functions which return a "likeness" score."""
from typing import Callable, Dict, Hashable, Iterable, Literal, Set, TypeVar

H = TypeVar("H", bound=Hashable)
NamesLiteral = Literal["heuristic", "equality", "like_database_table", "modified_hamming"]
MappingScoreFunction = Callable[[H, Set[H]], Iterable[float]]
"""Signature for a likeness score function.

Args:
    name: An element to find matches for.
    candidates: Potential matches for `value`.

Keyword Args:
    kwargs: Accepted only by some functions.

Yields:
    A score for each candidate `c` in `candidates`.
"""


def like_database_table(name: str, candidates: Iterable[str]) -> Iterable[float]:
    """Try to make `value` look like the name of a database table."""

    def apply(s: str) -> str:
        s = s.lower().replace("_", "").replace(".", "")
        return s if s.endswith("s") else s + "s"

    if name.endswith("id"):
        name = name[:-2]
    name = apply(name)

    yield from modified_hamming(
        name=name,
        candidates=list(map(apply, candidates)),
    )


def modified_hamming(name: str, candidates: Iterable[str]) -> Iterable[float]:
    """Compute hamming distance modified by candidate length, in reverse."""
    rev = tuple(reversed(name))

    def _apply(candidate: str) -> float:
        same = 0
        count = 0
        for a, b in zip(reversed(candidate), rev):
            same += int(a == b)  # Works find without explicit int-cast, but black removes parentheses changing the ast
            count += 1

        return count * same / len(candidate)

    yield from map(_apply, candidates)


def equality(value: H, candidates: Iterable[H]) -> Iterable[float]:
    """Return 1.0 if ``k == c_i``, 0.0 otherwise.

    Args:
        value: An element to find matches for.
        candidates: Potential matches for `value`.

    Yields:
        A score for each candidate `c` in `candidates`.
    """
    yield from map(float, [value == c for c in candidates])


_functions: Dict[str, MappingScoreFunction] = {
    func.__name__: func for func in [like_database_table, equality, modified_hamming]  # type: ignore
}


def get(name: str) -> MappingScoreFunction:
    """Get a scoring function by name."""
    return _functions[name]
