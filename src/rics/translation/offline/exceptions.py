"""Offline translation exceptions."""


class OfflineError(ValueError):
    """Base class for offline translation errors."""


class MalformedPlaceholderError(OfflineError):
    """Indicates that a translation placeholder is malformed."""
