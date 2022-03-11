from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Union

from rics._internal_support.types import NO_DEFAULT, NoDefault
from rics.translation.offline import exceptions
from rics.translation.offline._format import Format
from rics.translation.offline._magic_dict import MagicDict
from rics.translation.offline.types import (
    IdType,
    NameType,
    PlaceholdersDict,
    PlaceholdersTuple,
    SourceType,
    TranslatedIds,
)
from rics.utility.misc import tname


class FormatApplier(ABC, Generic[IdType, NameType, SourceType]):
    """Base class for application of ``Format`` specifications.

    Args:
        source: Source for the translations.
        placeholders: A dict ``{placeholder: placeholders..}``.
        default: Default values for each key in `placeholders`.

    Raises:
        KeyError: If placeholder 'id' is missing from `placeholders`.
        MalformedPlaceholderError: For any placeholder `p` where ``len(placeholders[p]) != len(placeholders['id'])``.
        ValueError: If `default` is given and any placeholder names are missing.

    See Also:
        :class:`rics.translation.offline._format.Format`
    """

    def __init__(
        self, source: SourceType, placeholders: PlaceholdersDict, default: Union[NoDefault, Dict[str, Any]] = NO_DEFAULT
    ) -> None:
        if "id" not in placeholders:
            raise KeyError(f"Required placeholder 'id' missing. Placeholder names: {list(sorted(placeholders))}.")

        self._source: SourceType = source
        self._placeholder_names = list(sorted(placeholders))

        if default != NO_DEFAULT:
            for name in placeholders:
                if name != "id" and name not in default:
                    raise ValueError(f"Placeholder {name=} not present in {default=}.")

        self._default = default

        n_ids = len(placeholders["id"])
        for placeholder, values in placeholders.items():
            if len(values) != n_ids:
                raise exceptions.MalformedPlaceholderError(
                    f"{source}.{placeholder}: Number of values {len(values)} do not match the number of IDs {n_ids}."
                )
        self._n_ids = n_ids

    def __call__(self, fmt: Format, placeholders: PlaceholdersTuple = None) -> MagicDict[IdType]:
        """Translate IDs.

        Args:
            fmt: Translation format to use.
            placeholders: Placeholders to include in the formatted output. None=as many as possible.

        Returns:
            A dict ``{idx: translated_id}``.

        Raises:
            KeyError: If required placeholders for `fmt` are missing..
            KeyError: If any placeholders (placeholders) are missing for this ``FormatApplier``.
        """
        if placeholders is None:
            # Use as many placeholders as possible.
            placeholders = tuple(filter(self._placeholder_names.__contains__, fmt.placeholders))

        missing_required_placeholders = set(fmt.required_placeholders).difference(placeholders)
        if missing_required_placeholders:
            raise KeyError(missing_required_placeholders)  # pragma: no cover
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
    @abstractmethod
    def positional(self) -> bool:
        """If True, names are stripped from fstring placeholders."""

    @property
    def source(self) -> SourceType:
        """Return translation source."""
        return self._source  # pragma: no cover

    @property
    def placeholders(self) -> List[str]:
        """Return placeholder names in sorted order."""
        return self._placeholder_names.copy()  # pragma: no cover

    def __len__(self) -> int:
        return self._n_ids  # pragma: no cover

    def __repr__(self) -> str:
        placeholders = tuple(self._placeholder_names)
        source = self._source
        return f"{tname(self)}({len(self)} IDs, {placeholders=}, {source=})"


class DefaultFormatApplier(FormatApplier):
    """Default format applier implementation."""

    def __init__(
        self, source: SourceType, placeholders: PlaceholdersDict, default: Union[NoDefault, Dict[str, Any]] = NO_DEFAULT
    ) -> None:
        super().__init__(source, placeholders, default)
        self._placeholders = placeholders

    def _apply(self, fstring: str, placeholders: PlaceholdersTuple) -> TranslatedIds:
        ids = self._placeholders["id"]
        p_list = tuple([self._placeholders[p] for p in placeholders])
        return {idx: fstring.format(*row) for idx, row in zip(ids, zip(*p_list))}

    @property
    def positional(self) -> bool:
        """Positional-flag for the default applicator."""
        return True
