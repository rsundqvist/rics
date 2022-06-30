"""Cardinality exceptions."""


class CardinalityError(ValueError):
    """Raised for cardinality issues."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
