"""Types used for translation."""
from typing import TYPE_CHECKING, Callable, Dict, Hashable, Iterable, Sequence, TypeVar, Union

if TYPE_CHECKING:
    import pandas  # noqa: F401

Translatable = TypeVar("Translatable", "pandas.DataFrame", "pandas.Series", Dict, Sequence, str, int)
"""Enumeration of translatable types."""

ID: str = "id"
"""Name of the ID placeholder."""

NameType = TypeVar("NameType", bound=Hashable)
"""Type used to label collections of IDs, such as the column names in a DataFrame or the keys of a dict."""

IdType = TypeVar("IdType", int, str)
"""Type of the value being translated into human-readable labels."""

SourceType = TypeVar("SourceType", bound=Hashable)
"""Type used to describe sources. Typically a string for things like files and database tables."""

NamesPredicate = Callable[[NameType], bool]
"""A predicate type on names."""
NameTypes = Union[NameType, Iterable[NameType]]
"""A union of a name type, or an iterable thereof."""
Names = Union[NameTypes, NamesPredicate]
"""Acceptable name types."""
