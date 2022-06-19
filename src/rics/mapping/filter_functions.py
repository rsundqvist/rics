"""Functions which return filter candidates."""
import logging
from typing import Callable, Collection, Hashable, Iterable, List, Literal, Set, TypeVar

LOGGER = logging.getLogger(__name__)

WhereOptions = Literal["name", "candidate", "both"]
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

    The `where`-argument must be one of:

        * `'name'`: Require only that `name` starts with `prefix`. If it does, return all candidates,
            otherwise return any empty collection.
        * `'candidate'`: Require only that candidates start with `prefix`. Return those that do.
        * `'both'`: Require that both `name` and candidates start with `prefix`. If it does, return all candidates
            which also start with `prefix`. If `name` does not start with `prefix, return an empty collection.

    Args:
        name: A name.
        candidates: Potential matches for `name`.
        prefix: The prefix to look for.
        where: One of 'name', 'candidate' or 'both'. See above.

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

    The `where`-argument must be one of:

        * `'name'`: Require only that `name` ends with `suffix`. If it does, return all candidates,
            otherwise return any empty collection.
        * `'candidate'`: Require only that candidates end with `suffix`. Return those that do.
        * `'both'`: Require that both `name` and candidates end with `suffix`. If it does, return all candidates
            which also end with `suffix`. If `name` does not end with `suffix, return an empty collection.

    Args:
        name: A name.
        candidates: Potential matches for `name`.
        suffix: The suffix to look for.
        where: One of 'name', 'candidate' or 'both'. See above.

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


def banned_substring_in_name(name: str, candidates: Iterable[str], substrings: Collection[str]) -> Set[str]:
    """Prevent `name` from being mapped if it contains a banned substring.

    Args:
        name: An element to find matches for.
        candidates: Potential matches for `name` (not used).
        substrings: Substrings which may not be present in `name`.

    Returns:
        An empty collection if `name` contains any of the substrings in
        `substrings`, otherwise all candidates in `candidates`.
    """
    logger = LOGGER.getChild("banned_substring_in_name")

    substrings = _substrings_in_name(name, substrings)
    if substrings:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Refuse matching of {name=}, contains banned substrings: {sorted(substrings)}.")
        return set()

    return set(candidates)


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

    kept: List[str] = []
    triggering_substrings = set()

    for cand in candidates:
        for kw in substrings:
            if kw in cand:
                triggering_substrings.add(kw)
                kept.append(cand)

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


def _substrings_in_name(name: str, substrings: Collection[str]) -> Set[str]:
    return set(filter(name.__contains__, substrings))
