import logging
from typing import Any, Dict, Iterable, Optional, Union

from .. import log_split_progress
from .._docstrings import add_docstrings
from ..types import DatetimeSplitBounds, DatetimeSplits

LogProgressArg = Union[str, bool, Dict[str, Any], logging.Logger, logging.LoggerAdapter]

add_docstrings(log_progress="Controls logging of fold progress. See :func:`~.log_split_progress` for details.")


def handle_log_progress_arg(
    log_progress: LogProgressArg, *, splits: DatetimeSplits
) -> Optional[Iterable[DatetimeSplitBounds]]:
    """Wrapper function for integrations."""
    if log_progress is True:
        return log_split_progress(splits)
    elif isinstance(log_progress, (str, logging.Logger, logging.LoggerAdapter)):
        return log_split_progress(splits, logger=log_progress)
    elif isinstance(log_progress, dict):
        return log_split_progress(splits, **log_progress)

    return None
