"""Mapping errors."""


class MappingError(ValueError):
    """Something failed to map."""


class CardinalityError(MappingError):
    """Base class for cardinality issues."""


class MappingWarning(UserWarning):
    """Something failed to map."""


class BadFilterError(MappingError):
    """Invalid filter."""
