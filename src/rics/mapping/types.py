"""Types used for mapping."""
from typing import Callable, Dict, Hashable, Iterable, Optional, Set, Tuple, TypeVar, Union

HL = TypeVar("HL", bound=Hashable)
"""Hashable type on the left side of a directional relationship."""
HR = TypeVar("HR", bound=Hashable)
"""Hashable type on the right side of a directional relationship."""
DictMapping = Union[Dict[HL, (Tuple[HR, ...])], Dict[HR, (Tuple[HL, ...])]]
"""Type for a left-to-right or right-to-left directional relationship."""

MappedItemType = TypeVar("MappedItemType", bound=Hashable)
"""A type of item being mapped."""
MatchTuple = Tuple[MappedItemType, ...]
"""A tuple of candidates matched to a value."""
ContextType = TypeVar("ContextType", bound=Hashable)
"""Type of context in which mapping is being performed."""

UserOverrideFunction = Callable[[MappedItemType, Set[MappedItemType], Optional[ContextType]], Optional[MappedItemType]]
"""Signature for a user-defined override function.

Unlike static overrides, which are always accepted, the return value of an override function must be in `candidates` to
be considered valid.

Args:
    value: An element to find matches for.
    candidates: Potential matches for `value`.
    context: The context in which scoring is being performed.

Returns:
    Either None (let regular logic decide) or a single candidate `c` in `candidates`.
"""

ScoreFunction = Callable[[MappedItemType, Iterable[MappedItemType], Optional[ContextType]], Iterable[float]]
"""Signature for a likeness score function.

Args:
    value: An element to find matches for.
    candidates: Potential matches for `value`.
    context: The context in which scoring is being performed.

Keyword Args:
    kwargs: Accepted only by some functions.

Yields:
    A score for each candidate `c` in `candidates`.
"""

AliasFunction = Callable[
    [MappedItemType, Iterable[MappedItemType], Optional[ContextType]], Tuple[MappedItemType, Iterable[MappedItemType]]
]
"""Signature for an alias function for heuristic scoring.

Args:
    value: An element to find matches for.
    candidates: Potential matches for `value`.
    context: The context in which mapping is being performed.

Keyword Args:
    kwargs: Accepted only by some functions.

Returns:
    A tuple (name, candidates) with applied heuristics to increase (or decrease) score as desired.
"""

FilterFunction = Callable[[MappedItemType, Iterable[MappedItemType], Optional[ContextType]], Set[MappedItemType]]
"""Signature for a filter function.

Args:
    value: An element to find matches for.
    candidates: Potential matches for `value`.
    context: The context in which filtering is being performed.

Keyword Args:
    kwargs: Accepted only by some functions.

Returns:
    A subset of candidates to keep.
"""

HeuristicsTypes = Union[AliasFunction, FilterFunction]
"""Types that may be interpreted as a score function heuristic."""
