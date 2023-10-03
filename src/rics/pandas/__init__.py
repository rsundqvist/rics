"""Utility functions for :mod:`pandas`."""

from warnings import warn as _warn

from ._time_fold import DatetimeSplitter, TimeFold

__all__ = ["TimeFold", "DatetimeSplitter"]
_warn("This module has been deprecated. Use `rics.ml.time_split` instead.", category=DeprecationWarning)
