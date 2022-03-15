from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Union

from rics._internal_support.types import NO_DEFAULT, NoDefault
from rics.translation.offline._format import Format
from rics.translation.offline._magic_dict import MagicDict
from rics.translation.offline.types import (
    IdType,
    NameType,
    PlaceholdersTuple,
    PlaceholderTranslations,
    SourceType,
    TranslatedIds,
)
from rics.utility.misc import tname


class FormatApplier(ABC, Generic[IdType, NameType, SourceType]):
    """Base class for application of ``Format`` specifications.

    Args:
        placeholder_translations: Matrix of ID translation components returned by fetchers.
        default: Default values for each key in `placeholders`.

    Raises:
        ValueError: If `default` is given and any placeholder names are missing.

    See Also:
        :class:`rics.translation.offline._format.Format`
    """

    def __init__(
        self,
        placeholder_translations: PlaceholderTranslations,
        default: Union[NoDefault, Dict[str, Any]] = NO_DEFAULT,
    ) -> None:
        self._source = placeholder_translations.source
        self._placeholder_names = placeholder_translations.placeholders

        if default != NO_DEFAULT:
            for name in placeholder_translations.placeholders:
                if name != "id" and name not in default:
                    raise ValueError(f"Placeholder {name=} not present in {default=}.")

        self._default = default
        self._n_ids = len(placeholder_translations.records)

    def __call__(self, fmt: Format, placeholders: PlaceholdersTuple = None) -> MagicDict[IdType]:
        """Translate IDs.

        Args:
            fmt: Translation format to use.
            placeholders: Placeholders to include in the formatted output. None=as many as possible.

        Returns:
            A dict ``{idx: translated_id}``.
        """
        if placeholders is None:
            # Use as many placeholders as possible.
            placeholders = tuple(filter(self._placeholder_names.__contains__, fmt.placeholders))

        fstring = fmt.fstring(placeholders, positional=self.positional)

        return MagicDict.make(self._apply(fstring, placeholders), fstring, placeholders, self._default)

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
        """If True, names are stripped from fstring placeholders."""
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
        placeholder_translations: PlaceholderTranslations,
        default: Union[NoDefault, Dict[str, Any]] = NO_DEFAULT,
    ) -> None:
        super().__init__(placeholder_translations, default)
        self._pht = placeholder_translations

    def _apply(self, fstring: str, placeholders: PlaceholdersTuple) -> TranslatedIds:
        if self._placeholder_names == placeholders:
            return {record[self._pht.id_pos]: fstring.format(*record) for record in self._pht.records}
        else:
            pos = tuple(map(self._placeholder_names.index, placeholders))
            return {record[self._pht.id_pos]: fstring.format(*(record[i] for i in pos)) for record in self._pht.records}
