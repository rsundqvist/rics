"""Types used by the framework."""

import collections.abc as _abc
import typing as _t

DataType = _t.TypeVar("DataType")
"""A type of data accepted by candidate functions."""
CandFunc = _abc.Callable[[DataType], _t.Any]
"""A function ``(DataType) -> Any`` under test. The return value is ignored."""
ResultsDict = dict[str, dict[_t.Hashable, list[float]]]
"""A result set on the form ``{candidate_label: {data_label: [runtime, ...]}}``."""

Ts = _t.TypeVarTuple("Ts")
"""Argument types for a :attr:`DataFunc` callable."""
DataFunc = _abc.Callable[[*Ts], DataType]
"""A function ``(*Ts) -> DataType`` used to generate test data."""
