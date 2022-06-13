import logging
from abc import ABC, abstractmethod
from time import perf_counter
from typing import Any, Collection, Dict, Generic, Iterable, List, Optional, Sequence, Set, Tuple, Union

from rics.translation.exceptions import OfflineError
from rics.translation.fetching import exceptions
from rics.translation.fetching._fetch_instruction import FetchInstruction
from rics.translation.fetching._ids_to_fetch import IdsToFetch
from rics.translation.offline import PlaceholderOverrides
from rics.translation.offline.types import (
    IdType,
    NameType,
    PlaceholderOverridesDict,
    PlaceholdersTuple,
    PlaceholderTranslations,
    SourcePlaceholderTranslations,
    SourceType,
)
from rics.utility.misc import tname
from rics.utility.perf import format_perf_counter

LOGGER = logging.getLogger(__package__).getChild("Fetcher")


class Fetcher(ABC, Generic[NameType, IdType, SourceType]):
    """Base class for fetching translations from an external source.

    Users who wish to define their own fetching logic should inherit this class, but there are implementations for
    common uses cases. See :class:`~rics.translation.fetching.PandasFetcher` for a versatile base fetcher or
    :class:`~rics.translation.fetching.SqlFetcher` for a more specialized solution.

    Args:
        allow_fetch_all: If False, an error will be raised when :meth:`fetch_all` is called.
        placeholder_overrides: Placeholder name overrides. Used to adapt placeholder names in sources to wanted names.

    See Also:
        Related classes:

        * :class:`rics.translation.offline.Format`, the format specification.
        * :class:`rics.translation.offline.TranslationMap`, application of formats.
        * :class:`rics.translation.Translator`, the main user interface for translation.
    """

    _FETCH_ALL: str = "_FETCH_ALL"

    def __init__(
        self,
        allow_fetch_all: bool = True,
        placeholder_overrides: Union[PlaceholderOverrides, PlaceholderOverridesDict] = None,
    ) -> None:
        self._allow_fetch_all = allow_fetch_all
        self._overrides = _create_overrides(placeholder_overrides)

    @property
    def online(self) -> bool:
        """Return connectivity status. If False, no new translations may be fetched."""
        return True

    def assert_online(self) -> None:
        """Raise an error if offline.

        Raises:
            OfflineError: If not online.
        """
        if not self.online:
            raise OfflineError("disconnected")

    @property
    @abstractmethod
    def sources(self) -> List[SourceType]:
        """Source names known to the fetcher, such as ``cities`` or ``languages``."""
        raise NotImplementedError()

    @property
    def placeholder_overrides(self) -> Optional[PlaceholderOverrides]:
        """Return the override."""
        return self._overrides

    @property
    def allow_fetch_all(self) -> bool:
        """Flag indicating whether the :meth:`fetch_all` operation is permitted."""
        return self._allow_fetch_all

    def fetch(
        self,
        ids_to_fetch: Iterable[IdsToFetch],
        placeholders: Iterable[str] = (),
        required: Iterable[str] = (),
    ) -> SourcePlaceholderTranslations:
        """Fetch translations.

        Args:
            ids_to_fetch: Tuples (source, ids) to fetch. If ``ids=None``, retrieve data for as many IDs as possible.
            placeholders: All desired placeholders in preferred order.
            required: Placeholders that must be included in the response.

        Returns:
            A mapping ``{source: PlaceholderTranslations}`` for translation.

        Raises:
            UnknownPlaceholderError: For placeholder(s) that are unknown to the fetcher.
            UnknownSourceError: For sources(s) that are unknown to the fetcher.
            ForbiddenOperationError: If trying to fetch all IDs when not possible or permitted.
            ImplementationError: For errors made by the inheriting implementation.

        Notes:
            Placeholders are usually columns in relational database applications. These are the components which are
            combined to create ID translations. See :class:`rics.translation.offline.Format` documentation for details.
        """
        unknown_sources = set(t.source for t in ids_to_fetch).difference(self.sources)
        if unknown_sources:
            sources = self.sources
            raise exceptions.UnknownSourceError(f"Sources {unknown_sources} not recognized: Known {sources=}.")

        if not self.allow_fetch_all and any(t.ids is None for t in ids_to_fetch):
            raise exceptions.ForbiddenOperationError(self._FETCH_ALL)

        return self._fetch(ids_to_fetch, tuple(placeholders), set(required))

    def fetch_all(
        self,
        placeholders: Iterable[str] = (),
        required: Iterable[str] = (),
    ) -> SourcePlaceholderTranslations:
        """Fetch as much data as possible.

        Args:
            placeholders: All desired placeholders in preferred order.
            required: Placeholders that must be included in the response.

        Returns:
            A mapping ``{source: PlaceholderTranslations}`` for translation.

        Raises:
            ForbiddenOperationError: If fetching all IDs is not possible or permitted.
            UnknownPlaceholderError: For placeholder(s) that are unknown to the fetcher.
            ImplementationError: For errors made by the inheriting implementation.
        """
        if not self.allow_fetch_all:
            raise exceptions.ForbiddenOperationError(self._FETCH_ALL)

        ids_to_fetch = [IdsToFetch(source, None) for source in self.sources]
        return self._fetch(ids_to_fetch, tuple(placeholders), set(required))

    def _fetch(
        self,
        ids_to_fetch: Iterable[IdsToFetch],
        placeholders: PlaceholdersTuple,
        required_placeholders: Set[str],
    ) -> SourcePlaceholderTranslations:

        return {
            source: placeholder_translations
            for source, placeholder_translations in self._fetch_translations(
                ids_to_fetch, placeholders, required_placeholders
            )
        }

    def _fetch_translations(
        self,
        ids_to_fetch: Iterable[IdsToFetch],
        placeholders: PlaceholdersTuple,
        required_placeholders: Set[str],
    ) -> Iterable[Tuple[SourceType, PlaceholderTranslations]]:
        for itf in ids_to_fetch:
            reverse_mappings, instr = self._make_fetch_instruction(itf, placeholders, required_placeholders)

            start = perf_counter()
            placeholder_translations = self.fetch_placeholders(instr)
            if LOGGER.isEnabledFor(logging.DEBUG):
                _log_implementation_fetch_performance(placeholder_translations, start)

            if reverse_mappings is not None:
                # The mapping is only in reverse from the Fetchers point-of-view; we're mapping back to "proper" values.
                _remap_placeholder_translations(placeholder_translations, reverse_mappings)

            placeholder_translations.id_pos = placeholder_translations.placeholders.index("id")
            yield instr.source, placeholder_translations

    def _make_fetch_instruction(
        self,
        itf: IdsToFetch,
        placeholders: PlaceholdersTuple,
        required_placeholders: Set[str],
    ) -> Tuple[Optional[Dict[str, str]], FetchInstruction]:
        fetch_all_placeholders = not placeholders

        required_placeholders.add("id")
        if "id" not in placeholders:
            placeholders = ("id",) + placeholders

        if self._overrides:
            if LOGGER.isEnabledFor(logging.DEBUG):
                LOGGER.debug(self._overrides.reverse().info_string(itf.source))

            for_source = self._overrides.reverse()[itf.source]

            def remap(placeholder):  # noqa
                return for_source.get(placeholder, placeholder)

            placeholders = tuple(map(remap, placeholders))
            required_placeholders = set(map(remap, required_placeholders))

        return (
            None if not self._overrides else self._overrides[itf.source],
            FetchInstruction(
                source=itf.source,
                ids=None if not itf.ids else tuple(itf.ids),
                placeholders=placeholders,
                required=required_placeholders,
                all_placeholders=fetch_all_placeholders,
            ),
        )

    @abstractmethod
    def fetch_placeholders(self, instruction: FetchInstruction) -> PlaceholderTranslations:
        """Fetch translations.

        Args:
            instruction: A single instruction for IDs to fetch. If IDs is None, the fetcher should retrieve data for as
                many IDs as possible.

        Returns:
            Placeholder translation elements.

        Raises:
            UnknownPlaceholderError: If the placeholder is unknown to the fetcher.
        """
        raise NotImplementedError()

    def close(self) -> None:
        """Close the fetcher. Does nothing by default."""

    def get_id_placeholder(self, source: SourceType) -> str:
        """Get the ID placeholder name for `source`."""
        if not self._overrides:
            return "id"

        return self.placeholder_overrides.reverse()[source].get("id", "id") if self.placeholder_overrides else "id"

    @classmethod
    def make_and_verify(
        cls, instr: FetchInstruction, known_placeholders: Collection[str], records: Sequence[Sequence[Any]]
    ) -> PlaceholderTranslations:
        """Make a :class:`~rics.translation.offline.types.PlaceholderTranslations` instance from records.

        Convenience method meant for use by implementations.

        Args:
            instr: A fetch instruction.
            known_placeholders: Known placeholders for the `instr.source`.
            records: Records produced from the instruction.

        Returns:
            Placeholder translation elements.

        Raises:
            UnknownPlaceholderError: If required placeholders are missing.
            ImplementationError: If the underlying fetcher does not return enough IDs.
        """
        if instr.ids is not None and len(records) < len(set(instr.ids)):
            actual_len = len(records)
            minimum = len(set(instr.ids))
            raise exceptions.ImplementationError(f"Got {actual_len} records, expected at least {minimum}.")

        cls.verify_placeholders(instr, known_placeholders)
        return PlaceholderTranslations(instr.source, tuple(known_placeholders), records)

    @classmethod
    def verify_placeholders(cls, instr: FetchInstruction, known_placeholders: Collection[str]) -> None:
        """Verify required placeholders for a source.

        Convenience method meant for use by implementations.

        Args:
            instr: A fetch instruction.
            known_placeholders: Known placeholders for the `instr.source`.

        Raises:
            UnknownPlaceholderError: If required placeholders are missing.
        """
        missing = instr.required.difference(known_placeholders)
        if missing:
            source = instr.source
            raise exceptions.UnknownPlaceholderError(
                f"Required placeholders {missing} not recognized."
                f" For {source=}, known placeholders are: {known_placeholders}."
            )

    @classmethod
    def select_placeholders(cls, instr: FetchInstruction, known_placeholders: Collection[str]) -> List[str]:
        """Select as many known, requested placeholders as possible.

        Args:
            instr: A fetch instruction.
            known_placeholders: Known placeholders for the `instr.source`.

        Returns:
            Known placeholders in the desired order.

        Raises:
            UnknownPlaceholderError: If required placeholders are missing.
        """
        cls.verify_placeholders(instr, known_placeholders)
        return list(
            known_placeholders
            if instr.all_placeholders
            else filter(known_placeholders.__contains__, instr.placeholders)
        )


def _remap_placeholder_translations(pht: PlaceholderTranslations, overrides: Dict[str, str]) -> None:
    """Remap a dict of placeholders using `overrides`."""
    pht.placeholders = tuple(overrides.get(name, name) for name in pht.placeholders)


def _create_overrides(
    overrides: Optional[Union["PlaceholderOverrides", PlaceholderOverridesDict]]
) -> Optional["PlaceholderOverrides"]:
    """Create overrides from a dict, if given. Returns None if not."""
    if overrides is None or not overrides:
        return None

    if isinstance(overrides, PlaceholderOverrides):
        return overrides
    if isinstance(overrides, dict):
        return PlaceholderOverrides.from_dict(overrides)
    else:
        raise TypeError(f"{overrides} is not a a valid {tname(PlaceholderOverrides)}-specification.")


def _log_implementation_fetch_performance(pht: PlaceholderTranslations, start: float) -> None:
    elapsed = format_perf_counter(start)
    LOGGER.debug(f"Fetched {pht.placeholders} for {len(pht.records)} IDS from '{pht.source}' in {elapsed}.")
