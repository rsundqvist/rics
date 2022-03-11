"""Functions which return a "likeness" score.

All methods follow the same signature:

Args:
    name: An element to find matches for.
    candidates: Potential matches for `value`.

Keyword Args:
    Accepted only by some functions.

Yields:
    A score for each candidate `c` in `candidates`.
"""
from typing import Callable, Dict, Hashable, Iterable, Literal, Set, TypeVar

H = TypeVar("H", bound=Hashable)
MappingScoreFunction = Callable[[H, Set[H]], Iterable[float]]
NamesLiteral = Literal["heuristic", "equality", "like_database_table", "modified_hamming"]


def like_database_table(name: str, candidates: Iterable[str], apply_heuristics: bool = False) -> Iterable[float]:
    """Try to make `value` look like the name of a database table."""
    if apply_heuristics:
        name = name.lower().replace("_", "").replace(".", "")
        if name.endswith("id"):
            name = name[:-2]
        if not name.endswith("s"):
            name += "s"

        candidates = list(map(str.lower, candidates))

    yield from modified_hamming(name, candidates)


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
