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


SetupFunc: _t.TypeAlias = _abc.Callable[[DataType], DataType]
"""A callable ``(data) -> data`` run -- unmeasured -- before each timed repetition to produce a fresh input."""

StratifyFunc: _t.TypeAlias = _abc.Callable[[_t.Hashable], _abc.Hashable]
"""A callable ``(data_label) -> stratum_key`` grouping comparable variants; see :class:`.MultiCaseTimer`."""

# The key is ``Any`` (not ``Hashable``) so a plain ``dict[str, ...]`` literal is accepted: ``Mapping`` is invariant
# in its key type, so ``Mapping[Hashable, ...]`` would reject ``dict[str, ...]``.
StrataMapping: _t.TypeAlias = _abc.Mapping[_t.Any, _abc.Iterable[_t.Hashable]]
"""A precomputed grouping ``stratum_key -> data labels``. Any compatible mapping works; :class:`.Strata` is the
fitted variant returned by :meth:`.MultiCaseTimer.compute_strata` (it also records how it was derived)."""

StratifyArg: _t.TypeAlias = StratifyFunc | StrataMapping | int | _t.Literal["full", "auto"] | None
"""Valid `stratify` input types; see :meth:`.MultiCaseTimer.compute_strata`."""
