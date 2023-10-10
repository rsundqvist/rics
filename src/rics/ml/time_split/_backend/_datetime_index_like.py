from typing import Iterable, Iterator, Protocol, runtime_checkable

from pandas import Series

from ..types import DatetimeTypes


@runtime_checkable
class DatetimeIndexLike(Protocol, Iterable[DatetimeTypes]):
    """A type that behaves (sort of) like a pandas DatetimeIndex."""

    def __iter__(self) -> Iterator[DatetimeTypes]:
        ...

    def value_counts(self) -> Series:
        ...

    def min(self) -> DatetimeTypes:  # noqa: A003
        ...

    def max(self) -> DatetimeTypes:  # noqa: A003
        ...
