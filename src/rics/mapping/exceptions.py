"""Mapping errors."""


class MappingError(ValueError):
    """Something failed to map."""


class UserMappingError(ValueError):
    """A user-defined mapping function did something strange."""


class CardinalityError(MappingError):
    """Base class for cardinality issues."""


class MappingWarning(UserWarning):
    """Something failed to map."""


class UserMappingWarning(MappingWarning):
    """A user-defined mapping function did something strange."""


class BadFilterError(MappingError):
    """Invalid filter."""
