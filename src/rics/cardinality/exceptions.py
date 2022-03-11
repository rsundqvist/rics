"""Cardinality exceptions."""

from rics.cardinality._enum import Cardinality


class CardinalityError(ValueError):
    """Raised for cardinality issues.

    Args:
        message: An exception message.
        cardinality: A ``Cardinality``.
    """

    def __init__(self, message: str, cardinality: Cardinality) -> None:
        super().__init__(message)
        self.cardinality = cardinality
