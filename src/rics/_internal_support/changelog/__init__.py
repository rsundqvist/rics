"""Utility for splitting a ``CHANGELOG.md`` file into multiple pages.

Not mean for general consumption; this is used to split the ``rics`` changelog, and makes several assumptions about the
format which do not hold in general. Included here because it makes my life easier.
"""
from rics._internal_support.changelog._patch_notes import PatchNotes
from rics._internal_support.changelog._split_changelog import split_changelog
from rics._internal_support.changelog._write_changelog import write_changelog

__all__ = ["split_changelog", "PatchNotes", "write_changelog"]
