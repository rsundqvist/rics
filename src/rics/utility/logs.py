"""
A namespace for logging constants, and a wrapper :meth:`rics.utility.logs.basic_config` for the standard
:py:func:`logging.basicConfig`-method with defaults which are defined here.
"""  # noqa: D205, D400
import logging
from typing import Any, Dict, Tuple, Union

FORMAT: str = "%(asctime)s.%(msecs)03d [%(name)s:%(levelname)s] %(message)s"
"""Default logging format; ``logging.basicConfig(format=FORMAT)``

Sample: ``<date-format>.378 [rics:DEBUG] I'm a debug message!``
"""

DATE_FORMAT: str = "%Y-%m-%dT%H:%M:%S"
"""Default logging date format; ``logging.basicConfig(datefmt=DATE_FORMAT)``

Sample: ``2022-02-05T11:17:05<logging-format>``
"""


def basic_config(rics_level: Union[int, str] = None, force: bool = True, **kwargs: Any) -> None:
    """Do basic logging configuration with package defaults.

    Args:
        rics_level: Log level for the `rics` package. None=inherit.
        force: If True, override existing configuration if it exists.
        **kwargs: Keyword arguments for :py:func:`logging.basicConfig`.

    Keyword Args:
        <namespace>_level: Log level for the namespace denoted by `namespace` (without the `"_level"`-suffix).
            Use underscores instead of dots for submodules, eg ``module.submodule`` => ``module_submodule``.
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
