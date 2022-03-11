"""Translation-specific exceptions."""


class FetcherError(RuntimeError):
    """Base class for fetcher exceptions."""


class ForbiddenOperationError(FetcherError):
    """Exception indicating that the fetcher does not support an operation.

    Args:
        operation: The operation which was not supported.
    """

    def __init__(self, operation: str) -> None:
        super().__init__(f"Operation '{operation}' not supported by this fetcher.")


class ImplementationError(FetcherError):
    """An underlying implementation did something wrong."""


class UnknownPlaceholderError(FetcherError):
    """Caller requested unknown placeholder name(s)."""


class UnknownIdError(FetcherError):
    """Caller requested unknown id(s)."""


class UnknownSourceError(FetcherError):
    """Caller requested unknown source(s)."""
