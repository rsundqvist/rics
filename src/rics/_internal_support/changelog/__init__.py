"""Utility for splitting a ``CHANGELOG.md`` file into multiple pages.

Not mean for general consumption; this is used to split the ``rics`` changelog, and makes several assumptions about the
format which do not hold in general. Included here because it makes my life easier.
"""

from ._patch_notes import PatchNotes
from ._split_changelog import split_changelog
from ._write_changelog import write_changelog

__all__ = ["PatchNotes", "split_changelog", "write_changelog"]
