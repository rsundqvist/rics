"""Translation-specific exceptions."""
from typing import Iterable


class FetcherWarning(RuntimeWarning):
    """Base class for fetcher warnings."""


class FetcherError(RuntimeError):
    """Base class for fetcher exceptions."""


class ForbiddenOperationError(FetcherError):
    """Exception indicating that the fetcher does not support an operation.

    Args:
        operation: The operation which was not supported.
    """

    def __init__(self, operation: str, reason: str = "not supported by this fetcher.") -> None:
        super().__init__(f"Operation '{operation}' " + reason)
        self.operation = operation


class ImplementationError(FetcherError):
    """An underlying implementation did something wrong."""


class UnknownPlaceholderError(FetcherError):
    """Caller requested unknown placeholder name(s)."""


class UnknownIdError(FetcherError):
    """Caller requested unknown id(s)."""


class UnknownSourceError(FetcherError):
    """Caller requested unknown source(s)."""

    def __init__(self, unknown_sources: Iterable, sources: Iterable) -> None:
        super().__init__(f"Sources {set(unknown_sources)} not recognized: Known {sources=}.")


class DuplicateSourceWarning(FetcherWarning):
    """Duplicate sources detected."""


class DuplicateSourceError(FetcherError):
    """Multiple translations for the same source received."""
