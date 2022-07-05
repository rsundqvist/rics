"""Integration for insertion and extraction of IDs and translations to and from various data structures."""

from rics.translation.dio._data_structure_io import DataStructureIO
from rics.translation.dio._resolve import resolve_io

__all__ = ["DataStructureIO", "resolve_io"]
