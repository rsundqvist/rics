"""Utility methods for logging tasks."""

import logging as _logging
from contextlib import contextmanager as _contextmanager
from typing import Any as _Any

FORMAT: str = "%(asctime)s.%(msecs)03d [%(name)s:%(levelname)s] %(message)s"
"""Default logging format; ``<date-format>.378 [rics:DEBUG] I'm a debug message!``"""

DATE_FORMAT: str = "%Y-%m-%dT%H:%M:%S"
"""Default logging date format; ``2022-02-05T11:17:05<logging-format>``"""


def basic_config(
    *,
    format: str = FORMAT,
    datefmt: str = DATE_FORMAT,
    level: int | str = "INFO",
    force: bool = True,
    **kwargs: _Any,
) -> None:
    """Do basic logging configuration with package defaults.

    Simple wrapper for the standard :py:func:`logging.basicConfig`-method, using my personal preferences for defaults.

    Args:
        format: Format string for emitted messages; see :attr:`FORMAT`.
        datefmt: Format string for date/time; see :attr:`DATE_FORMAT`. If ``bool(datefmt)`` is ``False``, remove the
            time components if ``format == FORMAT`` (the default).
        level: Log level for the root logger.
        force: If ``True``, override existing configuration if it exists.
        **kwargs: Keyword arguments for :py:func:`logging.basicConfig`.

    Keyword Args:
        _level: Additional log levels to set, replacing *double* underscores with dots to produce the logger names. For
            example, passing ``rics__performance_level=logging.INFO`` will modify the `'rics.performance'`-logger.

    Examples:
        Basic usage.

        >>> import logging
        >>> basic_config(level=logging.INFO, rics_level=logging.DEBUG)
        >>> logging.getLogger("rics").debug("I'm a debug message!")
        >>> logging.debug("I'm a debug message!")
        >>> logging.critical("I'm a critical message!")  # Doctest: +SKIP
        2022-02-05T11:17:05.378 [rics:DEBUG] I'm a debug message!
        2022-02-05T11:17:05.378 [root:CRITICAL] I'm a critical message!

        Removing time from the message template. Setting ``datefmt=""`` works as well.

        >>> import sys
        >>> basic_config(datefmt=False, stream=sys.stdout)
        >>> logging.info("No time!")
        [root:INFO] No time!

    """
    if not datefmt and format == FORMAT:
        format = FORMAT.partition(" ")[-1]

    extra_levels, kwargs = _extract_extra_levels(**kwargs)
    _logging.basicConfig(level=level, format=format, datefmt=datefmt, force=force, **kwargs)

    for name, level in extra_levels.items():
        _logging.getLogger(name).setLevel(level)


@_contextmanager
def disable_temporarily(
    *loggers: str | _logging.Logger | _logging.LoggerAdapter,  # type: ignore[type-arg]
) -> _Any:
    """Temporarily disable logging.

    Args:
        *loggers: Loggers to disable.

    Yields:
        Nothing.

    Examples:
        Disable all logging temporarily.

        >>> import logging
        >>> logging.basicConfig()
        >>> with disable_temporarily(logging.root):
        ...     logging.info("This message is ignored.")

    """
    enabled_loggers: list[_logging.Logger] = []
    for logger in loggers:
        while isinstance(logger, _logging.LoggerAdapter):
            logger = logger.logger  # noqa: PLW2901
        if isinstance(logger, str):
            logger = _logging.getLogger(logger)  # noqa: PLW2901

        if not logger.disabled:
            enabled_loggers.append(logger)

    try:
        for logger in enabled_loggers:
            logger.disabled = True
        yield
    finally:
        for logger in enabled_loggers:
            logger.disabled = False


def _extract_extra_levels(
    **kwargs: _Any,
) -> tuple[dict[str, int | str], dict[str, _Any]]:
    levels: dict[str, int | str] = {}
    for key in list(kwargs.keys()):
        if key and key.endswith("_level"):
            wildcard_key = key.removesuffix("_level").replace("__", ".")

            level = kwargs.pop(key)
            if level is not None:  # pragma: no cover
                levels[wildcard_key] = level

    return levels, kwargs
