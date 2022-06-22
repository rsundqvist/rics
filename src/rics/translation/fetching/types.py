"""Types related to translation fetching."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Generic, Iterable, List, Optional, Set

from rics.translation.offline.types import (
    IdType,
    NameType,
    PlaceholdersTuple,
    SourcePlaceholderTranslations,
    SourceType,
)


@dataclass(frozen=True)
class IdsToFetch(Generic[SourceType, IdType]):
    """A source and the IDs to fetch from it.

    Attributes:
        source: Where to fetch from.
        ids: Unique IDs to fetch translations for. None=fetch as much as possible.
    """

    source: SourceType
    ids: Optional[Iterable[IdType]]


@dataclass(frozen=True)
class FetchInstruction(IdsToFetch[SourceType, IdType]):
    """Instructions given to an implementation.

    Tuples of this type are passed to the :meth:`_fetch_translations` method of fetcher implementations.

    Attributes:
        placeholders: All desired placeholders in preferred order.
        required: Placeholders that must be included in the response.
        all_placeholders: Flag indicated whether to retrieve as many placeholders as possible.
    """

    placeholders: PlaceholdersTuple
    required: Set[str]
    all_placeholders: bool


class Fetcher(ABC, Generic[NameType, IdType, SourceType]):
    """Interface for fetching translations from an external source."""

    @property
    @abstractmethod
    def allow_fetch_all(self) -> bool:
        """Flag indicating whether the :meth:`fetch_all` operation is permitted."""

    def close(self) -> None:
        """Close the fetcher. Does nothing by default."""

    @property
    @abstractmethod
    def online(self) -> bool:
        """Return connectivity status. If False, no new translations may be fetched."""

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

    @abstractmethod
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

    @abstractmethod
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
