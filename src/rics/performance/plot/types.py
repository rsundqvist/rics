"""Types used by the plotting framework."""

import typing as _t

from seaborn import FacetGrid as _FacetGrid

Candidate = _t.Literal["Candidate"]
TestData = _t.Literal["Test data"]
FuncOrData = Candidate | TestData

Kind = _t.Literal["bar", "box", "boxen", "point", "strip", "swarm", "violin"]
Unit = _t.Literal["s", "ms", "μs", "us", "ns"]


class Postprocessor(_t.Protocol):
    """A callable which applies fixups to a ``FacetGrid``."""

    def __call__(self, facet_grid: _FacetGrid) -> None:
        """Apply fixups to `facet_grid`."""
        pass
