"""Types used for offline translation."""
from dataclasses import dataclass
from typing import Any, Dict, Generic, Sequence, Tuple, TypeVar, Union

import pandas as pd

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

    def to_dict(self, max_rows: int = 0) -> Dict[str, Sequence[Any]]:
        """Create a dict representation of the translations."""
        records = self.records[:max_rows] if max_rows else self.records
        return {placeholder: [row[i] for row in records] for i, placeholder in enumerate(self.placeholders)}

    @staticmethod
    def to_dicts(
        source_placeholder_translations: "SourcePlaceholderTranslations[SourceType]",
        max_rows: int = 0,
    ) -> Dict[SourceType, Dict[str, Sequence[Any]]]:
        """Create a nested dict representation of the translations."""
        return {
            source: placeholder_translations.to_dict(max_rows)
            for source, placeholder_translations in source_placeholder_translations.items()
        }

    @staticmethod
    def from_dataframe(source: SourceType, data: pd.DataFrame) -> "PlaceholderTranslations":
        """Create instance from a pandas DataFrame."""
        return PlaceholderTranslations(
            source,
            placeholders=tuple(data),
            records=list(map(list, data.to_records(index=False))),
            id_pos=data.columns.get_loc("id") if "id" in data else -1,
        )

    @staticmethod
    def from_dict(source: SourceType, data: Dict[str, Sequence[Any]]) -> "PlaceholderTranslations":
        """Create instance from a dict."""
        return PlaceholderTranslations.from_dataframe(source, pd.DataFrame.from_dict(data))


SourcePlaceholderTranslations = Dict[SourceType, PlaceholderTranslations]  # {source: PlaceholderTranslations}
