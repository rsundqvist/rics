"""Types used for translation."""
from typing import TYPE_CHECKING, Callable, Dict, Hashable, Iterable, List, Optional, Sequence, Set, TypeVar, Union

if TYPE_CHECKING:
    import pandas  # noqa: F401

Translatable = TypeVar("Translatable", "pandas.DataFrame", "pandas.Index", "pandas.Series", Dict, Sequence, str, int)
"""Enumeration of translatable types."""

ID: str = "id"
"""Name of the ID placeholder."""

NameType = TypeVar("NameType", bound=Hashable)
"""Type used to label collections of IDs, such as the column names in a DataFrame or the keys of a dict."""

IdType = TypeVar("IdType", int, str)
"""Type of the value being translated into human-readable labels."""

SourceType = TypeVar("SourceType", bound=Hashable)
"""Type used to describe sources. Typically a string for things like files and database tables."""

ExtendedOverrideFunction = Callable[
    [NameType, Set[SourceType], List[IdType]], Optional[Union[SourceType, Dict[SourceType, List[IdType]]]]
]
"""Signature for a user-defined override function.

Args:
    name: A name to create a name-to-source match for.
    sources: Potential matches for `name`.
    ids: IDs for `name`.

Returns:
    Either ``None`` (let regular logic decide), a dict, or a source.

    If a dict, it is expected to be on the form ``{source: [ids_for_source..]}``.

See Also:
    The :attr:`rics.mapping.types.UserOverrideFunction` type.
"""

NamesPredicate = Callable[[NameType], bool]
"""A predicate type on names."""
NameTypes = Union[NameType, Iterable[NameType]]
"""A union of a name type, or an iterable thereof."""
Names = Union[NameTypes, NamesPredicate]
"""Acceptable name types."""
