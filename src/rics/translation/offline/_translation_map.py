from typing import Any, Dict, Generic, Iterator, List, Mapping, Tuple, Type, Union

from rics._internal_support.types import NO_DEFAULT
from rics.translation.offline import MagicDict
from rics.translation.offline._format import Format, FormatType
from rics.translation.offline._format_applier import DefaultFormatApplier, FormatApplier
from rics.translation.offline.types import IdType, NameToSourceDict, NameType, SourcePlaceholderTranslations, SourceType
from rics.utility.misc import tname


class TranslationMap(Mapping, Generic[NameType, IdType, SourceType]):
    """Storage class for fetched translations.

    Args:
        source_placeholder_translations: Fetched translations ``{source: PlaceholderTranslations}``.
        name_to_source: Mappings ``{name: source}``, but may be overridden by the user.
        fmt: A translation format. Must be given to use as a mapping.
        default: Per-source default values.
    """

    FORMAT_APPLIER_TYPE: Type[FormatApplier] = DefaultFormatApplier

    def __init__(
        self,
        source_placeholder_translations: SourcePlaceholderTranslations,
        name_to_source: NameToSourceDict = None,
        fmt: FormatType = None,
        default: Dict[SourceType, Dict[str, Any]] = None,
    ) -> None:
        default = default or {}

        self._source_formatters: Dict[SourceType, FormatApplier] = {
            source: self.FORMAT_APPLIER_TYPE(placeholder_translations, default.get(source, NO_DEFAULT))
            for source, placeholder_translations in source_placeholder_translations.items()
        }
        self.name_to_source = name_to_source or {}
        self._fmt = None if fmt is None else Format.parse(fmt)

    def apply(self, name: NameType, fmt: FormatType = None) -> MagicDict[IdType]:
        """Create translations for names. Note: ``__getitem__`` delegates to this method.

        Args:
            name: A name to translate.
            fmt: Format to use. If None, fall back to init format.

        Returns:
            Translations for `name` as a dict ``{id: translation}``.

        Raises:
            ValueError: If ``fmt==None`` and initialized without `fmt`.
            KeyError: If trying to translate `name` which is not known.
        """
        if fmt is None:  # pragma: no cover
            if self._fmt is None:
                raise ValueError("No format specified and none given at initialization.")
            else:
                fmt = self._fmt

        fmt = Format.parse(fmt)
        source = self.name_to_source[name]
        return self._source_formatters[source](fmt)

    @property
    def names(self) -> List[NameType]:
        """Return names that can be translated."""
        return list(self.name_to_source)

    @property
    def sources(self) -> List[SourceType]:
        """Return translation source."""
        return list(self._source_formatters)

    @property
    def name_to_source(self) -> NameToSourceDict:
        """Return name-to-source mapping."""
        return self._name_to_source

    @name_to_source.setter
    def name_to_source(self, value: NameToSourceDict) -> None:
        """Update bindings. Mappings name->source are always added, but may be overridden by the user."""
        source_to_source = {source: source for source in self.sources}
        self._name_to_source: NameToSourceDict = {**source_to_source, **value}

    def __getitem__(self, item: Union[NameType, Tuple[NameType, FormatType]]) -> MagicDict:
        name, fmt = item if isinstance(item, tuple) else (item, self._fmt)
        return self.apply(name, fmt)

    def __len__(self) -> int:
        return len(self.names)

    def __iter__(self) -> Iterator[NameType]:
        return iter(self.names)

    def __repr__(self) -> str:
        sources = ", ".join(
            {f"'{formatter.source}': {len(formatter)} IDs" for formatter in self._source_formatters.values()}
        )
        return f"{tname(self)}({sources})"
