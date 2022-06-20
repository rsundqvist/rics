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
        s = s.lower().replace("_", "").replace(".", "")
        return s if s.endswith("s") else s + "s"

    if name.endswith("id"):
        name = name[:-2]

    name = apply(name)

    yield from fn(name, map(apply, candidates))


def equality_with_affix(
    value: str,  # placeholder
    candidates: Iterable[str],  # columns
    add_table: bool = False,
    join_with: str = "_",
    prefixes: Collection[str] = (),
    suffixes: Collection[str] = (),
    table: str = "",
) -> Iterable[float]:
    """Return 1.0 if ``value == candidate`` or when combined given prefixes/affixes. Zero otherwise.

    This function is intended for column -> placeholder matching in database tables. Will not apply prefixes and
    suffixes at the same time. Exact matches are always preferred, and if one is found no other candidates will be given
    a non-zero score.

    Args:
        value: A placeholder to map to a column (=candidate).
        candidates: Potential matches for `value`.
        add_table: If True, add table to both prefixes and suffixes.
        join_with: A string which joins `value` with affixes.
        prefixes: Affixed before `value`.
        suffixes: Affixed after `value`.
        table: A table name. If given, it will be added to both `prefixes` and `suffixes`.

    Yields:
        A score for each candidate `c` in `candidates`.

    Raises:
        ValueError: If `add_table` is set by `table` is not given.
        ValueError: If none of `prefixes`, `suffixes` and `table` is are given, which is equivalent to regular equality.
    """
    if add_table:
        if not table:  # pragma: no cover
            raise ValueError(f"Got {add_table=} but no table was given.")
        prefixes = [table] + list(prefixes)
        suffixes = [table] + list(suffixes)

    if not (prefixes or suffixes):  # pragma: no cover
        raise ValueError("At least one of 'prefixes', 'suffixes' and 'table' must be given.")

    if value in candidates:
        for column in candidates:
            yield 1.0 if column == value else 0.0
        return

    for column in candidates:
        if prefixes and _match_with_affixes(prefixes, column, f"{{affix}}{join_with}{value}"):
            yield 1.0
        elif suffixes and _match_with_affixes(suffixes, column, f"{value}{join_with}{{affix}}"):
            yield 1.0
        else:
            yield 0.0


def _match_with_affixes(affixes: Collection[str], column: str, matcher: str) -> bool:
    return any((column == matcher.format(affix=affix)) for affix in affixes)


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
    equality_with_affix,
]
