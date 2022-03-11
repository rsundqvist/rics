"""Types used for offline translation."""

from typing import Any, Dict, Sequence, Tuple, TypeVar, Union

NameType = TypeVar("NameType", int, str)
IdType = TypeVar("IdType", int, str)
SourceType = TypeVar("SourceType", int, str)

PlaceholdersTuple = Tuple[str, ...]
NameToSourceDict = Dict[NameType, SourceType]  # {name: source}
PlaceholdersDict = Dict[str, Sequence[Any]]  # {source: {placeholder: [values..]}}
SourcePlaceholdersDict = Dict[SourceType, PlaceholdersDict]  # {source: {placeholder: [values..]}}
TranslatedIds = Dict[IdType, str]  # {id: translation}

# {"shared": {from_placeholder: to_placeholder}, "source-specific": {source: {from_placeholder: to_placeholder}}
PlaceholderOverridesDict = Dict[str, Union[Dict[str, str], Dict[str, Dict[str, str]]]]
