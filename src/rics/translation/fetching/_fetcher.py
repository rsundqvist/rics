import logging
from abc import ABC, abstractmethod
from time import perf_counter
from typing import Collection, Dict, Generic, Iterable, List, Optional, Set, Tuple, Union

from rics.translation.fetching import exceptions
from rics.translation.fetching._fetch_instruction import FetchInstruction
from rics.translation.fetching._ids_to_fetch import IdsToFetch
from rics.translation.offline import PlaceholderOverrides
from rics.translation.offline.exceptions import OfflineError
from rics.translation.offline.types import (
    IdType,
    NameType,
    PlaceholderOverridesDict,
    PlaceholdersDict,
    SourcePlaceholdersDict,
    SourceType,
)
from rics.utility.misc import format_perf_counter, tname

_FETCH_ALL = "FETCH_ALL"

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

    @placeholder_overrides.setter
    def placeholder_overrides(self, overrides: PlaceholderOverrides = None) -> None:
        self._overrides = overrides

    def fetch(
        self,
        ids_to_fetch: Iterable[IdsToFetch],
        required_placeholders: Iterable[str],
        optional_placeholders: Iterable[str],
    ) -> SourcePlaceholdersDict:
        """Fetch translations.

        Args:
            ids_to_fetch: Tuples (source, ids) to fetch. If ``ids=None``, retrieve data for as many IDs as possible.
            required_placeholders: Keys which must be present for every source.
            optional_placeholders: Keys which should be added if possible.

        Returns:
            A mapping ``{source: {placeholder: [values..]}}`` for translation.

        Raises:
            UnknownPlaceholderError: For placeholder(s) that are unknown to the fetcher.
            UnknownSourceError: For sources(s) that are unknown to the fetcher.
            ForbiddenOperationError: If trying to fetch all IDs when when not possible or permitted.
            ImplementationError: For errors made by the inheriting implementation.

        Notes:
            Placeholders are usually columns in relational database applications. These are the components which are
            combined to create ID translations. See :class:`rics.translation.offline.Format` documentation for details.
        """
        unknown_sources = set(t.source for t in ids_to_fetch).difference(self.sources)
        if unknown_sources:
            sources = self.sources
            raise exceptions.UnknownSourceError(f"Sources {unknown_sources} not recognized: Known {sources=}.")

        if not self._allow_fetch_all and any(t.ids is None for t in ids_to_fetch):
            raise exceptions.ForbiddenOperationError(_FETCH_ALL)

        return self._fetch(ids_to_fetch, set(required_placeholders), set(optional_placeholders))

    def fetch_all(
        self,
        required_placeholders: Iterable[str],
        optional_placeholders: Iterable[str],
    ) -> SourcePlaceholdersDict:
        """Fetch as much data as possible.

        Args:
            required_placeholders: Placeholder keys that must be present.
            optional_placeholders: Placeholder keys which should be added if possible.

        Returns:
            A mapping ``{source: {placeholder: [values..]}}`` for translation.

        Raises:
            ForbiddenOperationError: If fetching all IDs is not possible or permitted.
            UnknownPlaceholderError: For placeholder(s) that are unknown to the fetcher.
            ImplementationError: For errors made by the inheriting implementation.
        """
        if not self._allow_fetch_all:
            raise exceptions.ForbiddenOperationError(_FETCH_ALL)

        required_placeholders = set(required_placeholders)
        required_placeholders.add("id")

        ids_to_fetch = [IdsToFetch(source, None) for source in self.sources]
        return self._fetch(ids_to_fetch, required_placeholders, set(optional_placeholders))

    def _fetch(
        self,
        ids_to_fetch: Iterable[IdsToFetch],
        required_placeholders: Set[str],
        optional_placeholders: Set[str],
    ) -> SourcePlaceholdersDict:

        ans = {
            source: _ensure_with_id(source, placeholders_dict, ids_to_fetch, self)
            for source, placeholders_dict in self._fetch_translations(
                ids_to_fetch, required_placeholders, optional_placeholders
            )
        }

        return ans

    def _fetch_translations(
        self,
        ids_to_fetch: Iterable[IdsToFetch],
        required: Set[str],
        optional: Set[str],
    ) -> Iterable[Tuple[SourceType, PlaceholdersDict]]:
        for itf in ids_to_fetch:
            reverse_mappings, instr = self._make_fetch_instruction(itf, required, optional)

            start = perf_counter()
            placeholders_dict = self.fetch_placeholders(instr)
            if LOGGER.isEnabledFor(logging.DEBUG):
                _log_implementation_fetch_performance(itf, placeholders_dict, start)

            if reverse_mappings is not None:
                # The mapping is only in reverse from the Fetchers point-of-view; we're mapping back to "proper" values.
                placeholders_dict = _remap_placeholders_dict(placeholders_dict, reverse_mappings)

            self._verify_placeholders(instr.source, placeholders_dict, required)
            yield instr.source, placeholders_dict

    def _make_fetch_instruction(
        self, itf: IdsToFetch, required: Set[str], optional: Set[str]
    ) -> Tuple[Optional[Dict[str, str]], FetchInstruction]:
        if self._overrides:
            for_source = self._overrides.reverse()[itf.source]

            def remap(placeholder):  # noqa
                return PlaceholderOverrides.get_mapped_value(placeholder, for_source)

            required = set(map(remap, required))
            optional = set(map(remap, optional))

        return (
            None if not self._overrides else self._overrides[itf.source],
            FetchInstruction(
                itf.source,
                None if not itf.ids else tuple(itf.ids),
                tuple(required),
                tuple(optional),
            ),
        )

    @staticmethod
    def _verify_placeholders(source: SourceType, actual: Collection[str], required: Set[str]) -> None:
        unknown_required_placeholders = required.difference(actual)
        unknown_required_placeholders.discard("id")
        if unknown_required_placeholders:
            raise exceptions.UnknownPlaceholderError(
                f"Required placeholders {unknown_required_placeholders} not recognized."
                f" For {source=}, known placeholders are: {list(actual)}."
            )

    @abstractmethod
    def fetch_placeholders(self, instruction: FetchInstruction) -> PlaceholdersDict:
        """Fetch translations.

        Args:
            instruction: A tuple `(name, required_placeholders, optional_placeholders, ids)` to fetch. If ``ids=None``,
                the fetcher should retrieve data for as many IDs as possible.

        Returns:
            A dict ``{placeholder: [values..]}}``. The sequence should be ordered like `instruction.ids`.

        Raises:
            UnknownPlaceholderError: If the placeholder is unknown to the fetcher.
        """
        raise NotImplementedError()

    def close(self) -> None:
        """Close the fetcher."""


def _ensure_with_id(
    source: SourceType,
    placeholders_dict: PlaceholdersDict,
    ids_to_fetch: Iterable[IdsToFetch],
    impl: "Fetcher",
) -> PlaceholdersDict:
    if "id" not in placeholders_dict:
        ids = next(instr.ids for instr in filter(lambda instr: instr.source == source, ids_to_fetch))
        if ids is None:
            raise exceptions.ImplementationError(
                f"Implementation {tname(impl)}: '{impl}' did not return IDs for {source=} during a {_FETCH_ALL} "
                f"operation. Placeholders received: {list(placeholders_dict)}."
            )
        placeholders_dict["id"] = list(ids)
    return placeholders_dict


def _remap_placeholders_dict(placeholders_dict: PlaceholdersDict, overrides: Dict[str, str]) -> PlaceholdersDict:
    """Remap a dict of placeholders using `overrides`."""
    tmp = {}
    for name in placeholders_dict:
        reversed_name = PlaceholderOverrides.get_mapped_value(name, overrides)
        tmp[reversed_name] = placeholders_dict[name]
    return tmp


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
        raise TypeError(f"{overrides} is not a a valid {tname(PlaceholderOverrides)}.")


def _log_implementation_fetch_performance(itf: IdsToFetch, result: PlaceholdersDict, start: float) -> None:
    placeholders = tuple(sorted(result))
    elapsed = format_perf_counter(start)
    count = len(result[placeholders[0]])
    LOGGER.debug(f"Fetched placeholders: {placeholders} for {count} IDS from '{itf.source}' in {elapsed}.")
