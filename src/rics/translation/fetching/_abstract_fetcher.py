import logging
from abc import abstractmethod
from time import perf_counter
from typing import Any, Collection, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from rics.mapping import Mapper
from rics.translation.exceptions import OfflineError
from rics.translation.fetching import exceptions
from rics.translation.fetching.types import Fetcher, FetchInstruction, IdsToFetch
from rics.translation.offline.types import (
    IdType,
    NameType,
    PlaceholdersTuple,
    PlaceholderTranslations,
    SourcePlaceholderTranslations,
    SourceType,
)
from rics.utility.collections import InheritedKeysDict, reverse_dict
from rics.utility.perf import format_perf_counter

LOGGER = logging.getLogger(__package__).getChild("AbstractFetcher")


class AbstractFetcher(Fetcher[NameType, IdType, SourceType]):
    """Base class for fetching translations from an external source.

    Users who wish to define their own fetching logic should inherit this class, but there are implementations for
    common uses cases. See :class:`~rics.translation.fetching.PandasFetcher` for a versatile base fetcher or
    :class:`~rics.translation.fetching.SqlFetcher` for a more specialized solution.

    Args:
        mapper: A :class:`~rics.mapping.Mapper` instance used to adapt placeholder names in sources to wanted names, ie
            the names of the placeholders that are in the translation :class:`~rics.offline.Format` being used.
        allow_fetch_all: If False, an error will be raised when :meth:`fetch_all` is called.

    See Also:
        Related classes:

        * :class:`rics.translation.offline.Format`, the format specification.
        * :class:`rics.translation.offline.TranslationMap`, application of formats.
        * :class:`rics.translation.Translator`, the main user interface for translation.
        * :class:`rics.mapping.Mapper`, in-source name to :class:`~rics.offline.Format` placeholder name mapping.
    """

    _FETCH_ALL: str = "FETCH_ALL"

    def __init__(
        self,
        mapper: Mapper = None,
        allow_fetch_all: bool = True,
    ) -> None:
        self._mapper = mapper or Mapper(**self.default_mapper_kwargs())
        if not self._mapper.context_sensitive_overrides:  # pragma: no cover
            raise ValueError("Mapper must have context-sensitive overrides (type InheritedKeysDict).")

        self._mapping_cache: Dict[SourceType, Dict[str, Optional[str]]] = {}
        self._allow_fetch_all = allow_fetch_all

    def map_placeholders(
        self,
        source: SourceType,
        placeholders: Iterable[str],
        candidates: Iterable[str] = None,
        clear_cache: bool = False,
    ) -> Dict[str, Optional[str]]:
        """Map `placeholder` names to the actual names used in `source`.

        Args:
            source: The source to map placeholders for.
            placeholders: Desired placeholders, such as the output of :meth:`rics.offline.Format.placeholders`.
            candidates: A subset of candidates (placeholder names) in `source` to map with `placeholders`. None=retrieve
                using :meth:`get_placeholders`.
            clear_cache: If True, force a full remap.

        Returns:
            A dict ``{wanted_placeholder_name: actual_placeholder_name_in_source}``, where
            `actual_placeholder_name_in_source` will be None if the wanted placeholder could not be mapped to any of the
            candidates available for the source.
        """
        if clear_cache or source not in self._mapping_cache:
            self._mapping_cache[source] = {}
        ans = self._mapping_cache[source]

        self._mapper.candidates = set(self.get_placeholders(source) if candidates is None else candidates)
        placeholders = set(placeholders).difference(ans)  # Don't remap cached mappings

        for actual, wanted in self._mapper.apply(placeholders, context=source, source=source).left_to_right.items():
            ans[actual] = wanted[0]

        for not_mapped in placeholders.difference(ans):
            ans[not_mapped] = None

        return ans

    def id_column(self, source: SourceType, candidates: Iterable[str] = None) -> Optional[str]:
        """Return the ID column for `source`."""
        return self.map_placeholders(source, ["id"], candidates=candidates)["id"]

    @property
    def online(self) -> bool:
        """Return connectivity status. If False, no new translations may be fetched."""
        return True  # pragma: no cover

    def assert_online(self) -> None:
        """Raise an error if offline.

        Raises:
            OfflineError: If not online.
        """
        if not self.online:  # pragma: no cover
            raise OfflineError("disconnected")

    @property
    @abstractmethod
    def sources(self) -> List[SourceType]:
        """Source names known to the fetcher, such as ``cities`` or ``languages``."""

    @property
    @abstractmethod
    def placeholders(self) -> Dict[SourceType, List[str]]:
        """Placeholders for sources managed by the fetcher.

        Note that placeholders (and sources) are returned as they appear as they are known to the fetcher, without
        remapping to desired names. As an example, for sources ``cities`` and ``languages``, this property may return::

           placeholders = {
               "cities": ["city_id", "city_name", "location_id"],
               "languages": ["id", "name"],
           }

        Returns:
            A dict ``{source: placeholders_for_source}``.
        """

    def get_placeholders(self, source: SourceType) -> List[str]:
        """Get placeholders for `source`."""
        placeholders = self.placeholders
        if source not in placeholders:
            raise exceptions.UnknownSourceError({source}, self.sources)
        return placeholders[source]

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
        """Retrieve placeholder translations from the source.

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
            raise exceptions.UnknownSourceError(unknown_sources, self.sources)

        if not self.allow_fetch_all and any(t.ids is None for t in ids_to_fetch):  # pragma: no cover
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

    @abstractmethod
    def fetch_translations(self, instruction: FetchInstruction) -> PlaceholderTranslations:
        """Retrieve placeholder translations from the source.

        Args:
            instruction: A single instruction for IDs to fetch. If IDs is None, the fetcher should retrieve data for as
                many IDs as possible.

        Returns:
            Placeholder translation elements.

        Raises:
            UnknownPlaceholderError: If the placeholder is unknown to the fetcher.
        """

    def close(self) -> None:
        """Close the fetcher. Does nothing by default."""

    @classmethod
    def from_records(
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
            ImplementationError: If the underlying fetcher does not return enough IDs.
        """
        if instr.ids is not None and len(records) < len(set(instr.ids)):
            actual_len = len(records)
            minimum = len(set(instr.ids))
            raise exceptions.ImplementationError(f"Got {actual_len} records, expected at least {minimum}.")

        return PlaceholderTranslations(instr.source, tuple(known_placeholders), records)

    @classmethod
    def select_placeholders(cls, instr: FetchInstruction, known_placeholders: Collection[str]) -> List[str]:
        """Select as many known placeholders as possible."""
        return list(
            known_placeholders
            if instr.all_placeholders
            else filter(known_placeholders.__contains__, instr.placeholders)
        )

    @classmethod
    def default_mapper_kwargs(cls) -> Dict[str, Any]:
        """Create a default Mapper for fetcher implementations."""
        return dict(score_function="score_with_heuristics", overrides=InheritedKeysDict())

    def _fetch(
        self,
        ids_to_fetch: Iterable[IdsToFetch],
        placeholders: PlaceholdersTuple,
        required_placeholders: Set[str],
    ) -> SourcePlaceholderTranslations:

        return {
            source: translations
            for source, translations in self._fetch_translations(ids_to_fetch, placeholders, required_placeholders)
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
            translations = self.fetch_translations(instr)
            if LOGGER.isEnabledFor(logging.DEBUG):
                _log_implementation_fetch_performance(translations, start)

            if reverse_mappings:
                # The mapping is only in reverse from the Fetchers point-of-view; we're mapping back to "proper" values.
                translations.placeholders = tuple(reverse_mappings.get(p, p) for p in translations.placeholders)

            translations.id_pos = translations.placeholders.index("id")
            yield instr.source, translations

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

        wanted_to_actual = self._make_mapping(itf, placeholders, required_placeholders)

        actual_to_wanted: Dict[str, str] = reverse_dict(wanted_to_actual)
        need_placeholder_mapping = actual_to_wanted != wanted_to_actual
        if need_placeholder_mapping:
            placeholders = tuple(map(wanted_to_actual.__getitem__, filter(wanted_to_actual.__contains__, placeholders)))
            required_placeholders = set(map(wanted_to_actual.__getitem__, required_placeholders))

        return (
            actual_to_wanted if need_placeholder_mapping else None,
            FetchInstruction(
                source=itf.source,
                ids=None if not itf.ids else tuple(itf.ids),
                placeholders=placeholders,
                required=required_placeholders,
                all_placeholders=fetch_all_placeholders,
            ),
        )

    def _make_mapping(
        self, itf: IdsToFetch, placeholders: PlaceholdersTuple, required_placeholders: Set[str]
    ) -> Dict[str, str]:
        wanted_to_actual = self.map_placeholders(itf.source, placeholders)
        if LOGGER.isEnabledFor(logging.DEBUG):
            LOGGER.debug(f"Placeholder mappings for source={repr(itf.source)}: {wanted_to_actual}.")

        ans: Dict[str, str] = {wanted: actual for wanted, actual in wanted_to_actual.items() if actual}
        missing = required_placeholders.difference(ans)
        if missing:
            source = itf.source
            raise exceptions.UnknownPlaceholderError(
                f"Required placeholders {missing} not recognized."
                f" For {source=}, known placeholders are: {sorted(ans)}."
            )
        return ans


def _log_implementation_fetch_performance(pht: PlaceholderTranslations, start: float) -> None:  # pragma: no cover
    elapsed = format_perf_counter(start)
    LOGGER.debug(f"Fetched {pht.placeholders} for {len(pht.records)} IDS from '{pht.source}' in {elapsed}.")
