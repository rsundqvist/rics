from copy import copy
from typing import Any, Dict, Generic, Iterator, List, Mapping, Optional, Tuple, Type, Union

from rics.translation.offline import MagicDict
from rics.translation.offline._format import Format, FormatType
from rics.translation.offline._format_applier import DefaultFormatApplier, FormatApplier
from rics.translation.offline.types import NameToSourceDict, SourcePlaceholderTranslations
from rics.translation.types import IdType, NameType, SourceType
from rics.utility.collections.dicts import InheritedKeysDict, reverse_dict
from rics.utility.misc import tname


class TranslationMap(Mapping, Generic[NameType, SourceType, IdType]):
    """Storage class for fetched translations.

    Args:
        source_translations: Fetched translations ``{source: PlaceholderTranslations}``.
        name_to_source: Mappings ``{name: source}``, but may be overridden by the user.
        fmt: A translation format. Must be given to use as a mapping.
        default_fmt: Alternative format specification to use instead of `fmt` for fallback translation.
        default_fmt_placeholders: Per-source default placeholder values.

    Notes:
        Type checking of `fmt` and `default_fmt_placeholders` attributes may fail due to
        `mypy#3004 <https://github.com/python/mypy/issues/3004>`_
    """

    FORMAT_APPLIER_TYPE: Type[FormatApplier] = DefaultFormatApplier
    """Format application implementation type. Overwrite attribute to customize."""

    def __init__(
        self,
        source_translations: SourcePlaceholderTranslations,
        name_to_source: NameToSourceDict = None,
        fmt: FormatType = None,
        default_fmt: FormatType = None,
        default_fmt_placeholders: InheritedKeysDict[SourceType, str, Any] = None,
    ) -> None:
        self.default_fmt = default_fmt  # type: ignore
        self.default_fmt_placeholders = default_fmt_placeholders  # type: ignore
        self.fmt = fmt  # type: ignore
        self._source_formatters: Dict[SourceType, FormatApplier] = {
            source: TranslationMap.FORMAT_APPLIER_TYPE(translations)
            for source, translations in source_translations.items()
        }
        self.name_to_source = name_to_source or {}

        self._reverse_mode: bool = False

    def apply(self, name: NameType, fmt: FormatType = None, default_fmt: FormatType = None) -> MagicDict[IdType]:
        """Create translations for names. Note: ``__getitem__`` delegates to this method.

        Args:
            name: A name to translate.
            fmt: Format to use. If ``None``, fall back to init format.
            default_fmt: Alternative format for default translation. Resolution: Arg -> init arg, fmt arg, init fmt arg

        Returns:
            Translations for `name` as a dict ``{id: translation}``.

        Raises:
            ValueError: If ``fmt=None`` and initialized without `fmt`.
            KeyError: If trying to translate `name` which is not known.
        """
        if fmt is None:  # pragma: no cover
            if self._fmt is None:
                raise ValueError("No format specified and none given at initialization.")
            else:
                fmt = self._fmt

        fmt = Format.parse(fmt)
        default_fmt = self._default_fmt if default_fmt is None else Format.parse(default_fmt)
        source = self.name_to_source[name]
        translations = self._source_formatters[source](
            fmt, default_fmt=default_fmt, default_fmt_placeholders=self.default_fmt_placeholders.get(source)
        )
        return (
            MagicDict(reverse_dict(translations), default_value=translations.default_value)
            if self.reverse_mode
            else translations
        )

    @property
    def names(self) -> List[NameType]:
        """Return names that can be translated."""
        return list(self.name_to_source)

    @property
    def sources(self) -> List[SourceType]:
        """Return translation sources."""
        return list(self._source_formatters)

    @property
    def name_to_source(self) -> NameToSourceDict[NameType, SourceType]:
        """Return name-to-source mapping."""
        return self._name_to_source

    @name_to_source.setter
    def name_to_source(self, value: NameToSourceDict) -> None:
        """Update bindings. Mappings name->source are always added, but may be overridden by the user."""
        source_to_source = {source: source for source in self.sources}
        self._name_to_source: NameToSourceDict = {**source_to_source, **value}

    @property
    def fmt(self) -> Optional[Format]:
        """Return the translation format."""
        return self._fmt  # pragma: no cover

    @fmt.setter
    def fmt(self, value: Optional[FormatType]) -> None:
        self._fmt = None if value is None else Format.parse(value)

    @property
    def default_fmt(self) -> Optional[Format]:
        """Return the format specification to use instead of `fmt` for fallback translation."""
        return self._default_fmt  # pragma: no cover

    @default_fmt.setter
    def default_fmt(self, value: Optional[FormatType]) -> None:
        self._default_fmt = None if value is None else Format.parse(value)

    @property
    def default_fmt_placeholders(self) -> InheritedKeysDict:
        """Return the default translations used for `default_fmt_placeholders` placeholders."""
        return self._default_fmt_placeholders

    @default_fmt_placeholders.setter
    def default_fmt_placeholders(self, value: Optional[InheritedKeysDict]) -> None:
        self._default_fmt_placeholders = InheritedKeysDict() if value is None else InheritedKeysDict.make(value)

    @property
    def reverse_mode(self) -> bool:
        """Return reversed mode status flag.

         If set, the mappings returned by :meth:`apply` (and therefore also ``__getitem__`` are reversed.

        Returns:
            Reversal status flag.
        """
        return self._reverse_mode

    @reverse_mode.setter
    def reverse_mode(self, value: bool) -> None:
        self._reverse_mode = value

    def copy(self) -> "TranslationMap[NameType, SourceType, IdType]":
        """Make a copy of this ``TranslationMap``."""
        return copy(self)

    def __getitem__(self, item: Union[NameType, Tuple[NameType, FormatType]]) -> MagicDict:
        name, fmt = item if isinstance(item, tuple) else (item, self._fmt)
        return self.apply(name, fmt)

    def __len__(self) -> int:
        return len(self.names)

    def __iter__(self) -> Iterator[NameType]:
        return iter(self.names)  # pragma: no cover

    def __repr__(self) -> str:
        sources = ", ".join(
            {f"'{formatter.source}': {len(formatter)} IDs" for formatter in self._source_formatters.values()}
        )
        return f"{tname(self)}({sources})"
