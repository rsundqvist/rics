"""General errors for the translation suite."""


class ConfigurationError(ValueError):
    """Raised in case of bad configuration."""


class OfflineError(ValueError):
    """Raised for offline state errors."""
