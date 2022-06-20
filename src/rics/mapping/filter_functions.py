"""Functions which return filter candidates."""
import logging
from typing import Callable, Collection, Hashable, Iterable, List, Literal, Set, Tuple, TypeVar

LOGGER = logging.getLogger(__name__)

WhereOptions = Literal["name", "candidate", "both"]
"""
Determines how matching is done by various filter functions.

    * `'name'`: Require only that `name` matches, ignoring the candidates.
    * `'candidate'`: Require only that candidates match, ignoring the name.
    * `'both'`: Require that both `name` and candidates match.
"""
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


def require_prefix(name: str, candidates: Iterable[str], prefix: str, where: WhereOptions) -> Set[str]:
    """Require a prefix in `name` and/or `candidates`.

    Args:
        name: A name.
        candidates: Potential matches for `name`.
        prefix: The prefix to look for.
        where: One of 'name', 'candidate' or 'both'. See :const:`WhereOptions`.

    Returns:
        Candidates which pass the test.
    """
    logger = LOGGER.getChild("require_prefix")

    require_name = _parse_where_arg(where)
    if require_name and not name.startswith(prefix):
        logger.debug(f"Refuse matching of {name=}: Missing required {prefix=}.")
        return set()

    if where == "name":
        return set(candidates)

    kept: List[str] = []
    rejected: List[str] = []
    for cand in candidates:
        lst = kept if cand.startswith(prefix) else rejected
        lst.append(cand)

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Filtering with {prefix=} kept {sorted(kept)} and rejected {rejected}.")

    return set(kept)


def require_suffix(name: str, candidates: Iterable[str], suffix: str, where: WhereOptions) -> Set[str]:
    """Require a suffix in `name` and/or `candidates`.

    Args:
        name: A name.
        candidates: Potential matches for `name`.
        suffix: The suffix to look for.
        where: One of 'name', 'candidate' or 'both'. See :const:`WhereOptions`.

    Returns:
        Candidates which pass the test.
    """
    logger = LOGGER.getChild("require_suffix")

    require_name = _parse_where_arg(where)

    if require_name and not name.endswith(suffix):
        logger.debug(f"Refuse matching of {name=}: Missing required {suffix=}.")
        return set()

    if where == "name":
        return set(candidates)

    kept: List[str] = []
    rejected: List[str] = []
    for cand in candidates:
        lst = kept if cand.endswith(suffix) else rejected
        lst.append(cand)

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Filtering with {suffix=} kept {sorted(kept)} and rejected {rejected}.")

    return set(kept)


def banned_substring(
    name: str, candidates: Iterable[str], substrings: Collection[str], where: WhereOptions
) -> Set[str]:
    """Prevent mapping if banned substrings are found.

    Matching on `name` halts all mapping, whereas matching on a candidate excludes only those candidates that match.

    Args:
        name: An element to find matches for.
        candidates: Potential matches for `name` (not used).
        substrings: Substrings which may not be present in `name`.
        where: One of 'name', 'candidate' or 'both'. See :const:`WhereOptions`.

    Returns:
        An empty collection if `name` contains any of the substrings in
        `substrings`, otherwise all candidates in `candidates`.
    """
    logger = LOGGER.getChild("banned_substring")

    require_name = _parse_where_arg(where)

    substrings_in_name = _substrings_in_name(name, substrings)
    if substrings_in_name and require_name:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Refuse matching of {name=}, contains banned substrings: {sorted(substrings_in_name)}.")
        return set()

    candidates = set(candidates)

    if where == "name":
        return set(candidates)

    triggering_candidates, triggering_substrings = _match_with_substrings(candidates, substrings)

    if not triggering_substrings:
        return candidates

    kept = candidates.difference(triggering_candidates)

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            f"Removed candidates for {name=} that contain banned substrings "
            f"{triggering_substrings}: {sorted(triggering_substrings)}."
        )

    return set(kept)


def shortlisted_substring_in_candidate(name: str, candidates: Iterable[str], substrings: Collection[str]) -> Set[str]:
    """Shortlist candidates contains substrings that are shared with `name`.

    Args:
        name: An element to find matches for.
        candidates: Potential matches for `name`.
        substrings: Substrings in both `value` and `candidates` that trigger shortlisting.

    Returns:
        A subset of candidates that contain any of the substrings `substrings`, or all candidates of none of them do.
    """
    logger = LOGGER.getChild("shortlisted_substring_in_candidate")

    candidates = set(candidates)
    substrings = _substrings_in_name(name, substrings)

    if not substrings:
        return candidates

    kept, triggering_substrings = _match_with_substrings(candidates, substrings)

    if not triggering_substrings:
        return candidates

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            "Shortlisting candidates that share substrings "
            f"{sorted(triggering_substrings)} with {name=}: {sorted(kept)}."
        )

    return set(kept)


def _parse_where_arg(where: str) -> bool:
    options = ("name", "candidate", "both")
    if where not in options:
        raise ValueError(f"Bad {where=} argument: Not in {options=}.")

    return where != "candidate"


def _match_with_substrings(candidates: Iterable[str], substrings: Collection[str]) -> Tuple[List[str], List[str]]:
    triggering_candidates = []
    triggering_substrings = []

    for cand in candidates:
        for subs in substrings:
            if subs in cand:
                triggering_substrings.append(subs)
                triggering_candidates.append(cand)

    return triggering_candidates, triggering_substrings


def _substrings_in_name(name: str, substrings: Collection[str]) -> Set[str]:
    return set(filter(name.__contains__, substrings))
