"""Types used by the framework."""

import typing as _t

DataType = _t.TypeVar("DataType")
"""A type of data accepted by candidate functions."""
CandFunc = _t.Callable[[DataType], _t.Any]
"""A function ``(DataType) -> Any`` under test. The return value is ignored."""
ResultsDict = dict[str, dict[_t.Hashable, list[float]]]
"""A result set on the form ``{candidate_label: {data_label: [runtime, ...]}}``."""
