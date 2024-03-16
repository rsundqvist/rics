from collections.abc import Iterable, Iterator
from typing import Protocol, runtime_checkable

from pandas import Series

from ..types import DatetimeTypes


@runtime_checkable
class DatetimeIndexLike(Protocol, Iterable[DatetimeTypes]):
    """A type that behaves (sort of) like a pandas DatetimeIndex."""

    def __iter__(self) -> Iterator[DatetimeTypes]: ...

    def value_counts(self) -> Series: ...

    def min(self) -> DatetimeTypes: ...

    def max(self) -> DatetimeTypes: ...
