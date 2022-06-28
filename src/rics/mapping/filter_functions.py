"""Functions which return filter candidates."""
import logging
import re
from typing import Callable, Collection, Hashable, Iterable, List, Literal, Set, Tuple, TypeVar, Union

LOGGER = logging.getLogger(__name__)

WhereOptions = Literal["name", "source", "candidate"]
WHERE_OPTIONS = ("name", "candidate", "source")
WhereArg = Union[WhereOptions, Iterable[WhereOptions]]
"""Determines how where matches must be found during filtering operations."""
H = TypeVar("H", bound=Hashable)
FilterFunction = Callable[[H, Set[H]], Set[H]]
"""Signature for a filter function.

Args:
    name: An element to find matches for.
    candidates: Potential matches for `value`.

Keyword Args:
    kwargs: Accepted only by some functions.

Returns:
    A subset of candidates to keep.
"""


def require_regex_match(
    name: str,
    candidates: Iterable[str],
    regex: Union[str, re.Pattern],
    where: WhereArg,
    source: str = "",
    keep_if_match: bool = True,
) -> Set[str]:
    """Require a regex match in `name`, `source`, and/or `candidates`.

    Args:
        name: A name.
        candidates: Potential matches for `name`.
        regex: A regex pattern to pass to :py:func:`re.compile`.
        where: Which of ('name', 'candidate', 'source') to match in.
        source: A source (table) name. Ignored if empty.
        keep_if_match: If False, require that `regex` does _not_ match to keep candidates.

    Returns:
        Approved candidates.

    Raises:
        ValueError: If `where` contains `'source'` when `source` is not given.

    See Also:
        The :meth:`banned_substring` method.
    """
    where = _parse_where_args(where)

    if "source" in where and not source:  # pragma: no cover
        raise ValueError(f"Source not given but 'source' was found in {where=}.")

    pattern = re.compile(regex, flags=re.IGNORECASE) if isinstance(regex, str) else regex
    logger = LOGGER.getChild("require_regex_match")
    candidates = set(candidates)

    # Short-circuit full refusal
    if "name" in where:
        match = pattern.match(name)
        if keep_if_match and not match:
            logger.debug(f"Refuse matching of {name=}: Does not match {pattern=}.")
            return set()
        if match and not keep_if_match:
            logger.debug(f"Refuse matching of {name=}: Matches {pattern=}.")
            return set()

    if "source" in where:
        match = pattern.match(source)
        if keep_if_match and not match:
            logger.debug(f"Refuse matching of {source=}: Does not match {pattern=}.")
            return set()
        if match and not keep_if_match:
            logger.debug(f"Refuse matching of {source=}: Matches {pattern=}.")
            return set()

    if "candidate" not in where:
        return candidates

    kept: List[str] = []
    rejected: List[str] = []
    for cand in candidates:
        lst = kept if (bool(pattern.match(cand)) is keep_if_match) else rejected
        lst.append(cand)

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Filtering with {keep_if_match=} and {pattern=}; kept {sorted(kept)}, rejected {rejected}.")

    return set(kept)


def banned_substring(
    name: str,
    candidates: Iterable[str],
    substrings: Collection[str],
    where: WhereArg,
    source: str = "",
) -> Set[str]:
    """Prevent mapping if banned substrings are found.

    Matching on `name` or `source` halts all mapping. Matching candidates excludes only those candidates.

    Args:
        name: An element to find matches for.
        candidates: Potential matches for `name` (not used).
        substrings: Substrings which may not be present in `name`.
        where: Which of ('name', 'candidate', 'source') to match in. Empty=all.
        source: A source (table) name.

    Returns:
        Approved candidates.

    See Also:
        The :meth:`require_regex_match` method, which performs the actual work.
    """
    where = _parse_where_args(where)

    remaining = set(candidates)

    for subs in substrings:
        if not remaining:
            break

        matches = require_regex_match(
            name,
            remaining,
            regex=re.compile(f".*{subs}.*", flags=re.IGNORECASE),
            where=where,
            source=source,
            keep_if_match=False,
        )
        remaining = remaining.intersection(matches)

    return remaining


def _parse_where_args(args: WhereArg) -> Tuple[WhereOptions, ...]:
    if not args:
        raise ValueError(f"At least one of {WHERE_OPTIONS} must be given.")

    args_tuple = tuple((args,) if isinstance(args, str) else tuple(args))
    for where in args_tuple:
        if where not in WHERE_OPTIONS:
            raise ValueError(f"Bad where-argument {repr(args)}; {where=} not in {WHERE_OPTIONS}.")
    return args_tuple
