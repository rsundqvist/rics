"""Utility methods for logging tasks."""

import logging as _l
import typing as _t
from contextlib import contextmanager as _contextmanager

BASE_FORMAT = "[%(name)s:%(levelname)s] %(message)s"
FORMAT_MS: str = "%(asctime)s.%(msecs)03d " + BASE_FORMAT
"""Default logging format; ``<date-format>.378 [rics:DEBUG] I'm a debug message!``"""
FORMAT = FORMAT_MS  # Backwards compatibility
"""Alias of :attr:`FORMAT_MS`."""
FORMAT_SEC: str = "%(asctime)s " + BASE_FORMAT
"""Like :attr:`FORMAT_MS`, but without milliseconds; ``<date-format> [rics:DEBUG] I'm a debug message!``"""

DATE_FORMAT: str = "%Y-%m-%dT%H:%M:%S"
"""Default logging date format; ``2022-02-05T11:17:05<logging-format>``"""

LogLevel = int | str
"""Valid input types for :func:`convert_log_level`."""


def basic_config(
    *,
    format: str = FORMAT_MS,
    datefmt: str = DATE_FORMAT,
    level: LogLevel | None = "INFO",
    force: bool = True,
    **kwargs: _t.Any,
) -> None:
    """Do basic logging configuration with package defaults.

    Simple wrapper for the standard :py:func:`logging.basicConfig`-method, using my personal preferences for defaults.

    Args:
        format: Format string for emitted messages; see :attr:`FORMAT_MS`.
        datefmt: Format string for date/time; see :attr:`DATE_FORMAT`. If empty, remove the time components if
         ``format == FORMAT_MS`` (default) or ``FORMAT_SEC``.
        level: Log level for the root logger.
        force: If ``True``, override existing configuration if it exists.
        **kwargs: Keyword arguments for :py:func:`logging.basicConfig`.

    Keyword Args:
        _level: Additional log levels to set, replacing *double* underscores with dots to produce the logger names. For
            example, passing ``rics__performance_level=logging.INFO`` (or the dotted-name equivalent
            ``**{"rics.performance_level": "INFO"}``) will invoke
            :meth:`logging.getLogger("rics.performance").setLevel(logging.INFO) <logging.Logger.setLevel>`.

    Examples:
        Basic usage.

        >>> import logging
        >>> basic_config(level=logging.INFO, rics_level=logging.DEBUG)
        >>> logging.getLogger("rics").debug("I'm a debug message!")
        >>> logging.debug("I'm a debug message!")
        >>> logging.critical("I'm a critical message!")  # Doctest: +SKIP
        2022-02-05T11:17:05.378 [rics:DEBUG] I'm a debug message!
        2022-02-05T11:17:05.378 [root:CRITICAL] I'm a critical message!

        Removing time from the message template.

        >>> import sys
        >>> basic_config(datefmt="", stream=sys.stdout)
        >>> logging.info("No time!")
        [root:INFO] No time!

        Note that this only works when `format` is either :attr:`FORMAT_MS` or :attr:`FORMAT_SEC`.
    """
    if datefmt == "" and format in {FORMAT_MS, FORMAT_SEC}:
        format = BASE_FORMAT

    extra_levels, kwargs = _extract_extra_levels(**kwargs)
    _l.basicConfig(level=level, format=format, datefmt=datefmt, force=force, **kwargs)

    for name, extra_level in extra_levels.items():
        _l.getLogger(name).setLevel(extra_level)


@_contextmanager
def disable_temporarily(
    *loggers: str | _l.Logger | _l.LoggerAdapter,  # type: ignore[type-arg]
) -> _t.Any:
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
    enabled_loggers: list[_l.Logger] = []
    for logger in loggers:
        while isinstance(logger, _l.LoggerAdapter):
            logger = logger.logger  # noqa: PLW2901
        if isinstance(logger, str):
            logger = _l.getLogger(logger)  # noqa: PLW2901

        if not logger.disabled:
            enabled_loggers.append(logger)

    try:
        for logger in enabled_loggers:
            logger.disabled = True
        yield
    finally:
        for logger in enabled_loggers:
            logger.disabled = False


class LogLevelError(Exception):
    """Raised by :func:`convert_log_level`."""

    def __init__(self, log_level: LogLevel, argument_name: str, extra_notes: _t.Collection[str] = ()) -> None:
        super().__init__(f"Unknown {argument_name}={log_level!r}.")
        self._log_level = log_level
        self._argument_name = argument_name

        for note in extra_notes:
            self.add_note(note)

        self.add_note("Hint: Register this level using `logging.addLevelName()`.")

    @property
    def log_level(self) -> LogLevel:
        """Log level provided by user."""
        return self._log_level

    @property
    def argument_name(self) -> str:
        """Argument name seen by user."""
        return self._argument_name


def convert_log_level(
    log_level: LogLevel,
    *,
    verify: bool = False,
    name: str = "log_level",
) -> int:
    """Convert ``str`` or ``int`` to a valid log level.

    Args:
        log_level: Either ``str`` or ``int``.
        verify: If ``True`` and `log_level` is an ``int``, verify that `log_level` is a known level.
        name: Name to use in error messages.

    Returns:
        An integer level.

    See Also:
        The :func:`logging.addLevelName` function.

    Raises:
        LogLevelError: If `log_level` is an ``int`` without a known level name and ``verify=True``.
        LogLevelError: If `log_level` is a ``str`` without a known level name.
    """
    if isinstance(log_level, int):
        if verify and log_level not in _l._levelToName:
            verify = False
            raise LogLevelError(log_level, name, extra_notes=[f"Hint: Set `{verify=}` to allow."])

        return log_level

    name_to_level = _l._nameToLevel
    int_level = name_to_level.get(log_level)
    if int_level is None:
        upper = log_level.upper()
        extra_notes = [f"Hint: Did you mean {name}={upper!r}?"] if upper in name_to_level else []
        raise LogLevelError(log_level, name, extra_notes=extra_notes)

    return int_level


_UserLoggerArg = str | _l.Logger | _l.LoggerAdapter[_t.Any]
_UserVerbosityLevel = (
    _t.Mapping[str, LogLevel]
    | _t.Mapping[_l.Logger, LogLevel]
    | _t.Mapping[str | _l.Logger, LogLevel]
    | _t.Mapping[str | _l.LoggerAdapter[_t.Any], LogLevel]
    | _t.Mapping[_UserLoggerArg, LogLevel]
)
_UserVerbosityLevels = _t.Iterable[_UserVerbosityLevel]


class LoggingSetupHelper:
    """Helper class for logging configuration.

    Verbosity:
        Verbosity levels are assumed to be strictly increasing in the amount of logs emitted. In other words, `levels`
        such as

        >>> [{"id_translation": "DEBUG"}, {"id_translation": "INFO"}]

        are **not** permitted, since going from ``verbosity=1`` to ``verbosity=2`` would reduce the amount of legts
        emitted. Calling :meth:`LoggingSetupHelper.configure_logging` with ``verbosity=0`` disables logging entirely.

    Args:
        levels: An iterable of levels, where each level is a dict ``{logger_name: log_level}``.

        format: Format string for emitted messages; see :func:`rics.logs.basic_config`.
        datefmt: Format string for date/time; see :func:`rics.logs.basic_config`.

    .. note::

       You should `not` include the ``'_level'`` suffix that you would use when calling :func:`basic_config` directly.

    Raises:
        TypeError: If any `levels` are empty.
        ValueError: If `levels` is not strictly increasing in verbosity.
    """

    def __init__(
        self,
        levels: _UserVerbosityLevels,
        *,
        format: str = FORMAT_SEC,
        datefmt: str = DATE_FORMAT,
    ) -> None:
        self._levels = self._process_user_input_levels(levels)
        self._format = format
        self._datefmt = datefmt

    @property
    def max(self) -> int:
        """Maximum verbosity level."""
        return len(self._levels)

    def get_log_levels(self, verbosity: int) -> dict[str, int]:
        """Get log levels per logger at the given `verbosity` level.

        Args:
            verbosity: Verbosity level. Pass -1 for max level.

        Returns:
            A dict ``{logger: log_level}``

        Raises:
            ValueError: If `verbose` is zero, less than -1, or too high.
        """
        max_level = -1
        if verbosity in {max_level, self.max}:
            levels = self._levels
        elif verbosity == 0:
            raise ValueError(f"{verbosity=} = 0")
        elif verbosity < max_level:
            raise ValueError(f"{verbosity=} < -2")
        else:
            try:
                levels = self._levels[:verbosity]
            except IndexError:
                msg = f"Got {verbosity=}, but only {self.max} levels are defined."
                raise ValueError(msg) from None

        rv: dict[str, int] = {}
        for level_dict in reversed(levels):
            for name, level in level_dict.items():
                rv.setdefault(name, level)
        return rv

    @classmethod
    def _on_verbosity_zero(cls) -> None:
        _l.root.disabled = True  # Prevent last resort logging to stderr.

    def configure_logging(self, verbosity: int) -> None:
        """Configure logging using :func:`basic_config`.

        Args:
            verbosity: Verbosity level. Disable ``logging.root`` if zero.
        """
        if verbosity == 0:
            self._on_verbosity_zero()
            return

        kwargs = self.get_kwargs(verbosity)
        basic_config(**kwargs)

    def get_kwargs(self, verbosity: int) -> dict[str, _t.Any]:
        """Create kwargs for :func:`basic_config`.

        Args:
            verbosity: Verbosity level.

        Returns:
            A dict.
        """
        levels = self.get_log_levels(verbosity)
        kwargs: dict[str, _t.Any] = {f"{logger_name}_level": log_level for logger_name, log_level in levels.items()}
        return {
            **kwargs,
            "level": kwargs.pop("root", None),
            "format": self._format,
            "datefmt": self._datefmt,
        }

    def get_level_descriptions(self) -> list[str]:
        """Get lines describing the configured verbosity level.

        Returns one ``str`` item per level.

        Returns:
            A list of strings.
        """
        rv = []

        known_level_names = {*_l.getLevelNamesMapping()}

        seen: dict[str, int] = {}
        for verbosity in self._by_log_level():
            line = []
            for log_level, logger_names in verbosity.items():
                new_logger_names = []
                for name in logger_names:
                    if seen.get(name) != log_level:
                        new_logger_names.append(name)
                    seen[name] = log_level

                if new_logger_names:
                    name = _l.getLevelName(log_level)
                    name = f"{name} ({log_level})" if name in known_level_names else f"<no name> ({log_level})"
                    line.append(f"{' & '.join(new_logger_names)}: {name}")

            rv.append(", ".join(line))

        return rv

    def _by_log_level(self) -> list[dict[int, list[str]]]:
        rv = []

        for verbose in range(len(self._levels)):
            level_to_loggers: dict[int, list[str]] = {}
            for logger_name, log_level in self.get_log_levels(verbose + 1).items():
                level_to_loggers.setdefault(log_level, [])
                level_to_loggers[log_level].append(logger_name)

            level_to_loggers_sorted = {
                # Levels by descending verbosity (DEBUG=10, INFO=20, etc). Loggers by name.
                log_level: sorted(level_to_loggers[log_level])
                for log_level in sorted(level_to_loggers)
            }
            rv.append(level_to_loggers_sorted)

        return rv

    @classmethod
    def _process_user_input_levels(cls, user_verbosity_levels: _UserVerbosityLevels) -> list[dict[str, int]]:
        if not user_verbosity_levels:
            msg = "No levels given."
            raise TypeError(msg)

        seen: dict[str, int] = {}

        rv = []
        for i, user_dict in enumerate(user_verbosity_levels):
            if not user_dict:
                msg = f"Level {i + 1} (index={i}): No items."
                raise TypeError(msg)

            # Convert to fixed format, e.g. {"rics.performance": logging.INFO}.
            converted: dict[str, int] = {}
            for user_logger, user_log_level in user_dict.items():
                logger = cls._get_logger_name(user_logger, i)
                log_level = cls._log_level_as_int(user_log_level, logger, i)
                converted[logger] = log_level

            # Verify increasing verbosity.
            for name, new_log_level in converted.items():
                old_log_level = seen.get(name)
                if old_log_level is None:
                    continue
                if new_log_level < old_log_level:
                    continue

                old = f"{_l.getLevelName(old_log_level)} ({old_log_level})"
                new = f"{_l.getLevelName(new_log_level)} ({new_log_level})"
                msg = (
                    f"Level {i + 1} (index={i}), logger={name!r}: Found transition '{old} -> {new}'. "
                    "Log Level must decrease with increasing verbosity."
                )
                raise ValueError(msg)

            seen.update(converted)
            rv.append(converted)

        return rv

    @classmethod
    def _get_logger_name(cls, user_logger: _UserLoggerArg, index: int) -> str:
        logger = user_logger
        while hasattr(logger, "logger"):
            logger = logger.logger  # Unwrap adapters

        if isinstance(logger, str):
            return logger
        elif isinstance(logger, _l.Logger):
            return logger.name

        msg = f"Level {index + 1} ({index=}): Cannot derive name from {user_logger=}."
        raise TypeError(msg)

    @classmethod
    def _log_level_as_int(cls, user_log_level: LogLevel, user_logger: str, index: int) -> int:
        try:
            return convert_log_level(user_log_level, name=user_logger)
        except LogLevelError as e:
            msg = f"Level {index + 1} ({index=}): {e.args[0]}"
            raise ValueError(msg) from e


def _extract_extra_levels(
    **kwargs: _t.Any,
) -> tuple[dict[str, int], dict[str, _t.Any]]:
    levels: dict[str, int] = {}
    for key in list(kwargs.keys()):
        if key and key.endswith("_level"):
            wildcard_key = key.removesuffix("_level").replace("__", ".")

            level = kwargs.pop(key)
            if level is None:  # pragma: no cover
                continue

            log_level = convert_log_level(level, name=key)
            levels[wildcard_key] = log_level

    return levels, kwargs


LoggerArg = _l.Logger | str | None | _t.Literal[False]


@_t.overload
def get_logger(logger: LoggerArg) -> _l.Logger: ...
@_t.overload
def get_logger(logger: _l.LoggerAdapter[_t.Any]) -> _l.LoggerAdapter[_t.Any]: ...
def get_logger(logger: LoggerArg | _l.LoggerAdapter[_t.Any]) -> _l.Logger | _l.LoggerAdapter[_t.Any]:
    """Get a logger.

    Returns a :attr:`~logging.Logger.disabled` logger if `logger` is ``None``. Loggers and adapters are returned as-is.

    Args:
        logger: An adapter, logger, logger name, or ``None``.

    Returns:
        A logger instance.
    """
    if logger is None:
        logger = _l.getLogger("null")
        logger.disabled = True
        return logger

    if isinstance(logger, str):
        return _l.getLogger(logger)

    if isinstance(logger, (_l.Logger, _l.LoggerAdapter)):  # noqa: UP038  # Rule is deprecated. https://github.com/astral-sh/ruff/pull/16681
        return logger

    msg = f"{logger=} is not a logging.Logger"
    raise TypeError(msg)
