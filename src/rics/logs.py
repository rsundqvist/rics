"""Utility methods for logging tasks."""
import logging
from contextlib import contextmanager as _contextmanager
from typing import Any, Dict, List, Tuple, Union

FORMAT: str = "%(asctime)s.%(msecs)03d [%(name)s:%(levelname)s] %(message)s"
"""Default logging format; ``<date-format>.378 [rics:DEBUG] I'm a debug message!``"""

DATE_FORMAT: str = "%Y-%m-%dT%H:%M:%S"
"""Default logging date format; ``2022-02-05T11:17:05<logging-format>``"""


def basic_config(
    *,
    format: str = FORMAT,  # noqa: A002
    datefmt: str = DATE_FORMAT,
    level: Union[int, str] = logging.INFO,
    force: bool = True,
    **kwargs: Any,
) -> None:
    """Do basic logging configuration with package defaults.

    Simple wrapper for the standard :py:func:`logging.basicConfig`-method, using my personal preferences for defaults.

    Args:
        format: Format string for emitted messages; see :attr:`FORMAT`.
        datefmt: Format string for date/time; see :attr:`DATE_FORMAT`.
        level: Log level for the root logger. Default is ``logging.INFO``.
        force: If ``True``, override existing configuration if it exists.
        **kwargs: Keyword arguments for :py:func:`logging.basicConfig`.

    Keyword Args:
        _level: Additional log levels to set, replacing *double* underscores with dots to produce the logger names. For
            example, passing ``rics__performance_level=logging.INFO`` will modify the `'rics.performance'`-logger.

    Examples:
        Basic usage.

        >>> from rics.logs import basic_config, logging
        >>> basic_config(level=logging.INFO, rics_level=logging.DEBUG)
        >>> logging.getLogger("rics").debug("I'm a debug message!")
        >>> logging.debug("I'm a debug message!")
        >>> logging.critical("I'm a critical message!") # Doctest: +SKIP
        2022-02-05T11:17:05.378 [rics:DEBUG] I'm a debug message!
        2022-02-05T11:17:05.378 [root:CRITICAL] I'm a critical message!
    """
    extra_levels, kwargs = _extract_extra_levels(**kwargs)
    logging.basicConfig(level=level, format=format, datefmt=datefmt, force=force, **kwargs)

    for name, level in extra_levels.items():
        logging.getLogger(name).setLevel(level)


@_contextmanager
def disable_temporarily(  # type: ignore[no-untyped-def]
    logger: Union[logging.Logger, logging.LoggerAdapter],  # type:  ignore[type-arg]
    *more_loggers: Union[logging.Logger, logging.LoggerAdapter],  # type:  ignore[type-arg]
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
    loggers: List[logging.Logger] = []
    for lgr in (logger, *more_loggers):
        while isinstance(lgr, logging.LoggerAdapter):
            lgr = lgr.logger
        loggers.append(lgr)

    states = [lgr.disabled for lgr in loggers]

    try:
        for lgr in loggers:
            lgr.disabled = True
        yield
    finally:
        for lgr, old_state in zip(loggers, states):
            lgr.disabled = old_state


def logger_from_object(obj: Any, prefix_class: bool = True) -> logging.Logger:
    """Create logger from an object.

    Logger names are created based on ``type(obj)`` and the public module path.

    Args:
        obj: A logger to create an object for.
        prefix_class: If ``True``, prefix the name of the class for member objects.

    Returns:
        A logger.

    Examples:
        Class names are included for class members.

        >>> from logging import RootLogger
        >>> logger_from_object(RootLogger(level=10).setLevel).name
        'logging.Logger.setLevel'

        Top-level objects appear as you would expect them to.

        >>> logger_from_object(logger_from_object).name
        'rics.logs.logger_from_object'

        Exported members are shown using only public modules.

        >>> from rics._just_the_way_i_like_it import configure_stuff
        >>> logger_from_object(configure_stuff).name
        'rics.configure_stuff'
    """
    from rics.misc import tname

    parts = []
    for part in obj.__module__.split("."):
        if part[0] == "_":
            break
        parts.append(part)
    parts.append(tname(obj, prefix_classname=prefix_class))
    return logging.getLogger(".".join(parts))


def _extract_extra_levels(**kwargs: Any) -> Tuple[Dict[str, Union[int, str]], Dict[str, Any]]:
    suffix = "_level"

    levels: Dict[str, Union[int, str]] = {}
    for key in list(kwargs.keys()):
        if key and key.endswith(suffix):
            wildcard_key = key[: -len(suffix)].replace("__", ".")

            level = kwargs.pop(key)
            if level is not None:  # pragma: no cover
                levels[wildcard_key] = level

    return levels, kwargs
