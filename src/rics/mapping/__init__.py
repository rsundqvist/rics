"""Mapping implementations for matching groups of elements.

For and introduction to mapping, see :ref:`mapping-primer`.
"""

from rics.mapping._cardinality import Cardinality
from rics.mapping._directional_mapping import DirectionalMapping
from rics.mapping._heuristic_score import HeuristicScore
from rics.mapping._mapper import Mapper

__all__ = [
    "Cardinality",
    "HeuristicScore",
    "DirectionalMapping",
    "Mapper",
]
