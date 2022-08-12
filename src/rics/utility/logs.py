"""Utility methods for logging tasks."""
import logging
from typing import Any, Dict, Tuple, Union

FORMAT: str = "%(asctime)s.%(msecs)03d [%(name)s:%(levelname)s] %(message)s"
"""Default logging format; ``<date-format>.378 [rics:DEBUG] I'm a debug message!``"""

DATE_FORMAT: str = "%Y-%m-%dT%H:%M:%S"
"""Default logging date format; ``2022-02-05T11:17:05<logging-format>``"""


def basic_config(
    *,
    format: str = FORMAT,  # noqa: A002
    datefmt: str = DATE_FORMAT,
    rics_level: Union[int, str] = None,
    force: bool = True,
    **kwargs: Any,
) -> None:
    """Do basic logging configuration with package defaults.

    Simple wrapper for the standard :py:func:`logging.basicConfig`-method, using my personal preferences for defaults.

    Args:
        format: Format string for emitted messages; see :attr:`FORMAT`.
        datefmt: Format string for date/time; see :attr:`DATE_FORMAT`.
        rics_level: Log level for the `rics` package. Inherit if ``None``.
        force: If ``True``, override existing configuration if it exists.
        **kwargs: Keyword arguments for :py:func:`logging.basicConfig`.

    Keyword Args:
        <namespace>_level: Log level for the namespace denoted by `namespace` (without the `"_level"`-suffix).
            Use underscores instead of dots for submodules, eg ``module.submodule`` => ``module_submodule``.

    Examples:
        Basic usage.

        >>> from rics.utility.logs import basic_config, logging
        >>> root_logger = logging.getLogger()
        >>> basic_config(level=logging.INFO, rics_level=logging.DEBUG)
        >>> logging.getLogger("rics").debug("I'm a debug message!")
        >>> root_logger.debug("I'm a debug message!")
        >>> root_logger.critical("I'm a critical message!") # Doctest: +SKIP
        2022-02-05T11:17:05.378 [rics:DEBUG] I'm a debug message!
        2022-02-05T11:17:05.378 [root:CRITICAL] I'm a critical message!

        The Python :py:mod:`logging` module was imported on the same line to save space.
    """
    wildcard_levels, kwargs = _extract_wildcards(rics_level=rics_level, force=force, **kwargs)

    kwargs["format"] = kwargs.get("format", FORMAT)
    kwargs["datefmt"] = kwargs.get("datefmt", DATE_FORMAT)
    logging.basicConfig(**kwargs)

    for name, level in wildcard_levels.items():
        logging.getLogger(name).setLevel(level)


_LOG_LEVEL_SUFFIX = "_level"


def _extract_wildcards(**kwargs: Any) -> Tuple[Dict[str, Union[int, str]], Dict[str, Any]]:
    wildcard_levels: Dict[str, Union[int, str]] = {}
    for key in list(kwargs.keys()):
        if key and key.endswith(_LOG_LEVEL_SUFFIX):
            wildcard_key = key[: -len(_LOG_LEVEL_SUFFIX)].replace("_", ".")
            level = kwargs.pop(key)
            if level is not None:  # pragma: no cover
                wildcard_levels[wildcard_key] = level

    return wildcard_levels, kwargs
