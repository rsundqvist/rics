"""Mapping implementations for matching groups of elements.

For and introduction to mapping, see :ref:`mapping-primer`.
"""

from warnings import warn as _warn

from ._cardinality import Cardinality
from ._directional_mapping import DirectionalMapping
from ._heuristic_score import HeuristicScore
from ._mapper import Mapper

__all__ = [
    "Cardinality",
    "HeuristicScore",
    "DirectionalMapping",
    "Mapper",
]

_warn("rics.mapping has been deprecated and will be removed in 4.0", category=PendingDeprecationWarning)
