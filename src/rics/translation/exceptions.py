"""General errors for the translation suite."""


class ConfigurationError(ValueError):
    """Raised in case of bad configuration."""


class OfflineError(ValueError):
    """Raised for offline state errors."""


class TranslationError(ValueError):
    """Base class for translator errors."""


class TooManyFailedTranslationsError(TranslationError):
    """Raised if too many IDs fail to translate."""
