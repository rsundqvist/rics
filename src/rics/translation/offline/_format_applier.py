from abc import ABC, abstractmethod
from typing import Any, Collection, Dict, Generic, List, Union

from rics._internal_support.types import NO_DEFAULT, NoDefault
from rics.translation.offline._format import Format
from rics.translation.offline._magic_dict import MagicDict
from rics.translation.offline.types import PlaceholdersTuple, PlaceholderTranslations, TranslatedIds
from rics.translation.types import ID, IdType, NameType, SourceType
from rics.utility.misc import tname


class FormatApplier(ABC, Generic[IdType, NameType, SourceType]):
    """Base class for application of ``Format`` specifications.

    Args:
        translations: Matrix of ID translation components returned by fetchers.
        default: Default values for each key in `placeholders`.
        required_placeholders: Placeholder names which must be present in `default`. All if ``None``.

    Raises:
        ValueError: If `default` is given and any placeholder names are missing.
    """

    def __init__(
        self,
        translations: PlaceholderTranslations,
        default: Union[NoDefault, Dict[str, Any]] = NO_DEFAULT,
        required_placeholders: Collection[str] = None,
    ) -> None:
        self._source = translations.source
        self._placeholder_names = translations.placeholders

        if default is not NO_DEFAULT:
            required_defaults = set(
                translations.placeholders if required_placeholders is None else required_placeholders
            )
            required_defaults.discard(ID)
            missing = required_defaults.difference(default)
            if missing:
                raise ValueError(f"Placeholder names {sorted(missing)} not present in {default=}.")

        self._default = default
        self._n_ids = len(translations.records)

    def __call__(self, fmt: Format, placeholders: PlaceholdersTuple = None, default_fmt: Format = None) -> MagicDict:
        """Translate IDs.

        Args:
            fmt: Translation format to use.
            placeholders: Placeholders to include in the formatted output. Use as many as possible if ``None``.
            default_fmt: Alternative format for default translation.

        Returns:
            A dict ``{idx: translated_id}``.
        """
        if placeholders is None:
            # Use as many placeholders as possible.
            placeholders = tuple(filter(self._placeholder_names.__contains__, fmt.placeholders))

        fstring = fmt.fstring(placeholders, self.positional)
        real_translations = self._apply(fstring, placeholders)

        if self._default is NO_DEFAULT:
            default_fstring = None
        else:
            default_fmt = default_fmt or fmt
            placeholders = tuple(filter(self._placeholder_names.__contains__, default_fmt.placeholders))
            m = {**self._default, ID: "{}"} if ID in placeholders else self._default
            default_fstring = default_fmt.fstring(placeholders).format(**m)

        return MagicDict(
            real_translations,
            default_fstring,
        )

    @abstractmethod
    def _apply(self, fstring: str, placeholders: PlaceholdersTuple) -> TranslatedIds:
        """Apply fstring to all IDs.

        The abstract class delegates ``__apply__``-invocations to this method after some input validation.

        Args:
            fstring: A format string.
            placeholders: Keys needed for the fstring, in the order in which they appear.

        Returns:
            A dict ``{idx: translated_id}``.
        """

    @property
    def positional(self) -> bool:
        """If ``True``, names are stripped from fstring placeholders."""
        return True

    @property
    def source(self) -> SourceType:
        """Return translation source."""
        return self._source  # pragma: no cover

    @property
    def placeholders(self) -> List[str]:
        """Return placeholder names in sorted order."""
        return list(self._placeholder_names)  # pragma: no cover

    def __len__(self) -> int:
        return self._n_ids  # pragma: no cover

    def __repr__(self) -> str:
        placeholders = tuple(self._placeholder_names)
        source = self._source
        return f"{tname(self)}({len(self)} IDs, {placeholders=}, {source=})"


class DefaultFormatApplier(FormatApplier):
    """Default format applier implementation."""

    def __init__(
        self,
        translations: PlaceholderTranslations,
        default: Union[NoDefault, Dict[str, Any]] = NO_DEFAULT,
        required_placeholders: Collection[str] = None,
    ) -> None:
        super().__init__(translations, default, required_placeholders)
        self._pht = translations

    def _apply(self, fstring: str, placeholders: PlaceholdersTuple) -> TranslatedIds:
        if self._placeholder_names == placeholders:
            return {record[self._pht.id_pos]: fstring.format(*record) for record in self._pht.records}
        else:
            pos = tuple(map(self._placeholder_names.index, placeholders))
            return {record[self._pht.id_pos]: fstring.format(*(record[i] for i in pos)) for record in self._pht.records}
