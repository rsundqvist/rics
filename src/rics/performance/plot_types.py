"""Types used by the plotting framework."""

import typing as _t
from collections.abc import Callable as _Callable

if _t.TYPE_CHECKING:
    try:
        from seaborn import FacetGrid
    except ImportError:
        FacetGrid = _t.Never

Candidate = _t.Literal["Candidate"]
TestData = _t.Literal["Test data"]
FuncOrData = Candidate | TestData
"""Valid axis preferences."""

Kind = _t.Literal["bar", "box", "boxen", "point", "strip", "swarm", "violin"]
"""Valid plot kinds."""
Unit = _t.Literal["s", "ms", "μs", "us", "ns"]
"""Valid time units."""
Aggregation = _t.Literal["min", "median", "mean"]
"""How to summarize the repeated timings of a single candidate/data pair into one number."""

Postprocessor = _Callable[["FacetGrid"], None]
"""A callable ``(FacetGrid) -> None`` which applies fixups to a :class:`seaborn.FacetGrid`."""
