"""Mapping errors."""
from typing import Any, Set


class MappingError(ValueError):
    """Something failed to map."""

    def __init__(self, msg: str) -> None:
        super().__init__(
            msg + "\n\nFor help, please refer to the "
            "https://rics.readthedocs.io/en/stable/documentation/mapping-primer.html page."
        )


class UserMappingError(MappingError):
    """A user-defined mapping function did something strange."""

    def __init__(self, msg: str, value: Any, candidates: Set[Any]) -> None:
        super().__init__(msg)
        self.value = value
        self.candidates = candidates


class CardinalityError(MappingError):
    """Base class for cardinality issues."""


class MappingWarning(UserWarning):
    """Something failed to map."""


class UserMappingWarning(MappingWarning):
    """A user-defined mapping function did something strange."""


class BadFilterError(MappingError):
    """Invalid filter."""
