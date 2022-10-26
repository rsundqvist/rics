from abc import ABC, abstractmethod
from typing import Dict, Generic, Iterable, List

from rics.translation.fetching.types import IdsToFetch
from rics.translation.offline.types import SourcePlaceholderTranslations
from rics.translation.types import IdType, SourceType


class Fetcher(ABC, Generic[SourceType, IdType]):
    """Interface for fetching translations from an external source."""

    @property
    @abstractmethod
    def allow_fetch_all(self) -> bool:
        """Flag indicating whether the :meth:`~rics.translation.fetching.Fetcher.fetch_all` operation is permitted."""

    def close(self) -> None:
        """Close the ``Fetcher``. Does nothing by default."""

    @property
    @abstractmethod
    def online(self) -> bool:
        """Return connectivity status. If ``False``, no new translations may be fetched."""

    @property
    @abstractmethod
    def sources(self) -> List[SourceType]:
        """Source names known to the ``Fetcher``, such as ``cities`` or ``languages``."""

    @property
    @abstractmethod
    def placeholders(self) -> Dict[SourceType, List[str]]:
        """Placeholders for sources managed by the ``Fetcher``.

        Returns:
            A dict ``{source: [placeholders..]}``.

        Notes:
            Placeholders (and sources) are returned as they appear as they are known to the fetcher (without mapping).
        """

    @abstractmethod
    def fetch(
        self,
        ids_to_fetch: Iterable[IdsToFetch[SourceType, IdType]],
        placeholders: Iterable[str] = (),
        required: Iterable[str] = (),
    ) -> SourcePlaceholderTranslations[SourceType]:
        """Retrieve placeholder translations from the source.

        Args:
            ids_to_fetch: Tuples (source, ids) to fetch. If ``ids=None``, retrieve data for as many IDs as possible.
            placeholders: All desired placeholders in preferred order.
            required: Placeholders that must be included in the response.

        Returns:
            A mapping ``{source: PlaceholderTranslations}`` for translation.

        Raises:
            UnknownPlaceholderError: For placeholder(s) that are unknown to the ``Fetcher``.
            UnknownSourceError: For sources(s) that are unknown to the ``Fetcher``.
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
    ) -> SourcePlaceholderTranslations[SourceType]:
        """Fetch as much data as possible.

        Args:
            placeholders: All desired placeholders in preferred order.
            required: Placeholders that must be included in the response.

        Returns:
            A mapping ``{source: PlaceholderTranslations}`` for translation.

        Raises:
            ForbiddenOperationError: If fetching all IDs is not possible or permitted.
            UnknownPlaceholderError: For placeholder(s) that are unknown to the ``Fetcher``.
            ImplementationError: For errors made by the inheriting implementation.
        """
