"""Types used for offline translation."""
from dataclasses import dataclass
from typing import Any, Dict, Generic, Sequence, Tuple, TypeVar, Union

NameType = TypeVar("NameType", int, str)
IdType = TypeVar("IdType", int, str)
SourceType = TypeVar("SourceType", int, str)

PlaceholdersTuple = Tuple[str, ...]
NameToSourceDict = Dict[NameType, SourceType]  # {name: source}
TranslatedIds = Dict[IdType, str]  # {id: translation}
# {"shared": {from_placeholder: to_placeholder}, "source-specific": {source: {from_placeholder: to_placeholder}}
PlaceholderOverridesDict = Dict[str, Union[Dict[str, str], Dict[str, Dict[str, str]]]]
DefaultTranslationsDict = Dict[str, Union[Dict[str, Any], Dict[str, Dict[str, Any]]]]


@dataclass
class PlaceholderTranslations(Generic[SourceType]):
    """Matrix of ID translation components returned by fetchers.

    Attributes:
        source: Source for the placeholders.
        placeholders: Names of placeholders in the order in which they appear in `records`.
        records: Response matrix of shape `N x M` where `N` is the number of IDs returned and `M` is the length of
            `placeholders`.
        id_pos: Position if the `"id"` placeholder in `placeholders`.
    """

    source: SourceType
    placeholders: PlaceholdersTuple
    records: Sequence[Sequence[Any]]
    id_pos: int = -1


SourcePlaceholderTranslations = Dict[SourceType, PlaceholderTranslations]  # {source: PlaceholderTranslations}
