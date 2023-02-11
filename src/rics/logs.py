"""Utility methods for logging tasks."""
import logging
from contextlib import contextmanager as _contextmanager
from typing import Any, Dict, Union

from .strings import without_suffix as _without_suffix

FORMAT: str = "%(asctime)s.%(msecs)03d [%(name)s:%(levelname)s] %(message)s"
"""Default logging format; ``<date-format>.378 [rics:DEBUG] I'm a debug message!``"""

DATE_FORMAT: str = "%Y-%m-%dT%H:%M:%S"
"""Default logging date format; ``2022-02-05T11:17:05<logging-format>``"""


def basic_config(
    *,
    format: str = FORMAT,  # noqa: A002
    datefmt: str = DATE_FORMAT,
    level: Union[int, str] = logging.INFO,
    rics_level: Union[int, str] = logging.INFO,
    id_translation_level: Union[int, str] = logging.WARNING,
    matplotlib_level: Union[int, str] = logging.WARNING,
    force: bool = True,
    **kwargs: Any,
) -> None:
    """Do basic logging configuration with package defaults.

    Simple wrapper for the standard :py:func:`logging.basicConfig`-method, using my personal preferences for defaults.

    Args:
        format: Format string for emitted messages; see :attr:`FORMAT`.
        datefmt: Format string for date/time; see :attr:`DATE_FORMAT`.
        level: Log level for the root logger. Default is ``logging.INFO``.
        rics_level: Log level for the :mod:`rics` package. Default is ``logging.INFO``.
        id_translation_level: Log level for the :mod:`id_translation` package. Default is ``logging.WARNING``.
        matplotlib_level: Log level for the :mod:`matplotlib` package. Default is ``logging.WARNING``.
        force: If ``True``, override existing configuration if it exists.
        **kwargs: Keyword arguments for :py:func:`logging.basicConfig`.

    Examples:
        Basic usage.

        >>> from rics.logs import basic_config, logging
        >>> root_logger = logging.getLogger()
        >>> basic_config(level=logging.INFO, rics_level=logging.DEBUG)
        >>> logging.getLogger("rics").debug("I'm a debug message!")
        >>> root_logger.debug("I'm a debug message!")
        >>> root_logger.critical("I'm a critical message!") # Doctest: +SKIP
        2022-02-05T11:17:05.378 [rics:DEBUG] I'm a debug message!
        2022-02-05T11:17:05.378 [root:CRITICAL] I'm a critical message!
    """
    logging.basicConfig(level=level, format=format, datefmt=datefmt, force=force, **kwargs)

    for name, level in _extract_wildcards(
        rics_level=rics_level,
        id_translation_level=id_translation_level,
        matplotlib_level=matplotlib_level,
    ).items():
        logging.getLogger(name).setLevel(level)


@_contextmanager
def disable_temporarily(  # type: ignore[no-untyped-def]
    logger: logging.Logger, *more_loggers: logging.Logger
):  # noqa: ANN201
    """Temporarily disable logging.

    Args:
        logger: A logger to disable.
        *more_loggers: Additional loggers to disable.

    Yields:
        Nothing.

    Examples:
        Disable all logging temporarily.

        >>> import logging
        >>> logging.basicConfig()
        >>> with disable_temporarily(logging.root):
        ...     logging.info("This message is ignored.")
    """
    loggers = [logger] + list(more_loggers)
    states = [lgr.disabled for lgr in loggers]

    try:
        for lgr in loggers:
            lgr.disabled = True
        yield
    finally:
        for lgr, old_state in zip(loggers, states):
            lgr.disabled = old_state


_LOG_LEVEL_SUFFIX = "_level"


def _extract_wildcards(**kwargs: Any) -> Dict[str, Union[int, str]]:
    wildcard_levels = {}
    for key in list(kwargs):
        if key and key.endswith(_LOG_LEVEL_SUFFIX):
            wildcard_key = _without_suffix(key, _LOG_LEVEL_SUFFIX)
            level = kwargs.pop(key)
            if level is not None:  # pragma: no cover
                wildcard_levels[wildcard_key] = level

    return wildcard_levels
