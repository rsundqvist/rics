"""Mapping errors."""


class MappingError(ValueError):
    """Something failed to map."""


class BadFilterError(MappingError):
    """Invalid filter."""
