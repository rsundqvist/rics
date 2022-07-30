"""Functions which perform heuristics for score functions.

See Also:
    The :class:`~rics.mapping.HeuristicScore` class.
"""
import re
from typing import Any, Iterable, List, Optional, Set, Tuple, Union

from rics.mapping import filter_functions as ff
from rics.mapping.types import ContextType

VERBOSE: bool = False
"""If ``True`` enable optional DEBUG-level log messages on each heuristic function invocation.

Notes:
    Not all functions have verbose messages.
"""


def like_database_table(
    name: str,
    candidates: Iterable[str],
    context: Optional[ContextType],
) -> Tuple[str, List[str]]:
    """Try to make `value` look like the name of a database table."""

    def apply(s: str) -> str:
        s = s.lower().replace("_", "").replace(".", "")
        s = s[: -len("id")] if s.endswith("id") else s
        s = s if s.endswith("s") else s + "s"
        return s

    return apply(name), list(map(apply, candidates))


def short_circuit_to_value(
    value: str,
    candidates: Iterable[str],
    context: Optional[str],
    regex: Union[str, re.Pattern],
    target: str,
) -> Set[str]:
    """Short circuit candidates which match a given `regex` a given to-value.

    Args:
        value: A value to map.
        candidates: Candidates for `value`.
        context: Context in which the function is being called.
        regex: A pattern in `candidates` which should trigger forced short-circuit matching.
        target: The target value. If ``value != to_value``, an empty set is always returned.

    Returns:
        Candidates which match `regex`, or an empty set.

    Notes:
        This is technically a filter function and may be used as such.
    """
    return (
        set()
        if value != target
        else ff.require_regex_match(
            value,
            candidates,
            context,
            regex,
            where="candidate",
            purpose=f"short-circuiting to value-{target=}",
        )
    )


def short_circuit_to_candidate(
    value: str,
    candidates: Iterable[str],
    context: Optional[str],
    regex: Union[str, re.Pattern],
    target: str,
) -> Set[str]:
    """Short circuit candidates which match a given `regex` to a given to-candidate.

    Args:
        value: A value to map.
        candidates: Candidates for `value`.
        context: Context in which the function is being called.
        regex: A pattern in `candidates` which should trigger forced short-circuit matching.
        target: A target candidate. Must be present in `candidates`, or empty set is always returned.

    Returns:
        Candidates which match `regex`, or an empty set.

    Notes:
        This is technically a filter function and may be used as such.
    """
    return (
        set()
        if target not in candidates
        else ff.require_regex_match(
            value,
            [target],
            context,
            regex,
            where="name",
            purpose=f"short-circuiting to candidate-{target=}",
        )
    )


def force_lower_case(
    value: str, candidates: Iterable[str], context: Optional[ContextType]
) -> Tuple[str, Iterable[str]]:
    """Force lower-case in `value` and `candidates`."""
    return value.lower(), list(map(str.lower, candidates))


def value_fstring_alias(
    value: str, candidates: Iterable[str], context: Optional[ContextType], fstring: str, **kwargs: Any
) -> Tuple[str, Iterable[str]]:
    """Return a value formatted by `fstring`.

    Args:
        value: Passed to `fstring.format` using the `value` placeholder key.
        candidates: Not used (returned as given).
        context: Context in which the function is being called.
        fstring: The format string to use.
        **kwargs: Additional keyword placeholders in `fstring`.

    Returns:
        A tuple (formatted_value, candidates).
    """
    return fstring.format(value=value, context=context, **kwargs), candidates


def candidate_fstring_alias(
    value: str, candidates: Iterable[str], context: Optional[ContextType], fstring: str, **kwargs: Any
) -> Tuple[str, Iterable[str]]:
    """Return candidates formatted by `fstring`.

    Args:
        value: Not used (returned as given).
        candidates: Passed to `fstring.format` using the `candidates` placeholder key.
        context: Context in which the function is being called.
        fstring: The format string to use.
        **kwargs: Additional keyword placeholders in `fstring`.

    Returns:
        A tuple (value, formatted_candidates).
    """
    return value, map(lambda c: fstring.format(candidate=c, **kwargs), candidates)
