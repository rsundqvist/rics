from collections.abc import Callable
from functools import update_wrapper
from typing import Any, Literal

import click

from rics.logs import DATE_FORMAT, FORMAT_SEC, LoggingSetupHelper, _UserVerbosityLevels

AnyCallable = Callable[..., Any]
Decorator = Callable[[AnyCallable], AnyCallable]
Mode = Literal["forward", "forward_both", "pop", "skip"]


class VerbosityParamType(click.types.IntParamType):
    name = "verbosity"

    def __init__(self, max: int) -> None:
        self._max = max

    def convert(self, value: Any, param: click.Parameter | None, ctx: click.Context | None) -> Any:
        inv_value: int = super().convert(value, param, ctx)
        if inv_value > self._max:
            self.fail(f"May be repeated at most {self._max} times (got {value}).", param, ctx)
        return inv_value


def logging_verbosity_option(
    *param_decls: str,
    mode: Mode = "pop",
    # Helper class params
    levels: _UserVerbosityLevels,
    format: str = FORMAT_SEC,
    datefmt: str = DATE_FORMAT,
    # Click params
    cls: type[click.Option] | None = None,
    **attrs: Any,
) -> Decorator:
    """Add a ``click`` option to a command.

    Mode options:
        * `forward`: Configure logging, then forward the parameter.
        * `forward_both`: Do **not** configure logging. Forward a tuple ``(verbosity, helper)`` instead.
        * `pop` (default): Configure logging and remove the parameter.
        * `skip`: Does **not** configure logging or create a helper. The parameter is forwarded.

    Args:
        *param_decls: Positional arguments to the constructor of ``cls``.
        mode: Logging setup mode. See above for options.
        levels: An iterable of levels, where each level is a dict ``{logger_name: log_level}``.
        format: Format string for emitted messages; see :func:`rics.logs.basic_config`.
        datefmt: Format string for date/time; see :func:`rics.logs.basic_config`.
        cls: Type of :class:`click.Option` to instantiate.
        **attrs: Passed as keyword arguments to the constructor of ``cls``.
            Defaults are provided for `help`, `count`, and `type`.

    Raises:
        TypeError: If `attrs` is incompatible with this method.

    See Also:
        The :func:`click.option` function and :meth:`rics.logs.LoggingSetupHelper` class.

    Examples:
        Decorating ``click`` commands.

        >>> import logging, click
        >>> @click.command
        >>> @logging_verbosity_option(
        ...     "--verbose", "-v",
        ...     levels=[
        ...         {"rics": "INFO", "id_translation": "WARNING"},
        ...         {"rics": "DEBUG"},
        ...     ],
        ... )
        >>> @click.pass_context
        >>> def cli(cxt: click.Context, verbose: int) -> None:
        >>>     print(verbose)
        >>>     print(logging.getLogger("rics"))
        >>>     print(logging.getLogger("id_translation"))

        When running this command, passing ``-vv`` increases `rics` verbosity to ``logging.DEBUG``.

        Advanced configuration with ``mode="forward_both"``.

        >>> import logging, click
        >>> from rics.logs import LoggingSetupHelper
        >>> @click.command
        >>> @logging_verbosity_option(
        ...     "--verbose", "-v",
        ...     mode="forward_both",
        ...     levels=[
        ...         {"rics": "INFO", "id_translation": "WARNING"},
        ...         {"rics": "DEBUG"},
        ...     ],
        ... )
        >>> @click.pass_context
        >>> def cli(
        ...     cxt: click.Context,
        ...     verbose: tuple[int, LoggingSetupHelper],
        ... ) -> None:
        >>>     verbosity, helper = verbose
        >>>     helper.configure_logging(verbosity)  # 0=logging.root.disabled=True
        >>>     if verbosity == 0:
        >>>         import os, sys
        >>>         sys.stdout = open(os.devnull, "w")
        >>>         cxt.meta["no_stdout"] = True

        In this mode, :meth:`.LoggingSetupHelper.configure_logging()` is not called before invoking ``cli()``. Above is
        a dummy program that disables ``sys.stdout`` if verbosity is zero (i.e. ``-v`` is repeated zero times).
    """
    helper = LoggingSetupHelper(levels, format=format, datefmt=datefmt)

    if "help" not in attrs:
        attrs["help"] = _create_help_string(helper.get_level_descriptions())

    if "count" in attrs:
        raise TypeError(f"{attrs['count']=} is not allowed.")
    attrs["count"] = True

    if "type" in attrs:
        raise TypeError(f"{attrs['type']=} is not allowed.")
    param_type = VerbosityParamType(helper.max)
    attrs["type"] = param_type

    click_option_decorator = click.option(*param_decls, cls=cls, **attrs)

    if mode == "skip":
        return click_option_decorator

    return _create_decorator(helper, click_option_decorator, param_type, mode)


def _create_decorator(
    helper: LoggingSetupHelper,
    click_decorator: Decorator,
    param_type: VerbosityParamType,
    mode: Mode,
) -> Decorator:
    def get_param_name(func: AnyCallable) -> str:
        assert hasattr(func, "__click_params__")  # noqa: S101
        cp: click.Parameter
        for cp in func.__click_params__:
            if cp.type is param_type:
                assert isinstance(cp.name, str)  # noqa: S101
                return cp.name

        raise RuntimeError(f"Unable to derive verbosity parameter name: {func.__click_params__=}.")

    def configure_logging_decorator(func: AnyCallable) -> AnyCallable:
        click_func = click_decorator(func)  # Sets __click_params__ on func.
        param_name = get_param_name(click_func)  # Could click_func be a click.Command at this point?

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            verbosity = kwargs.pop(param_name) if mode == "pop" else kwargs[param_name]
            if not isinstance(verbosity, int):
                raise TypeError(f"kwargs[{param_name!r}={kwargs[param_name]!r}: expected `int`")

            if mode == "forward_both":
                kwargs[param_name] = verbosity, helper
                return func(*args, **kwargs)

            helper.configure_logging(verbosity)
            return func(*args, **kwargs)

        return update_wrapper(wrapper, click_func)

    return configure_logging_decorator


def _create_help_string(descriptions: list[str]) -> str:
    """Create help string."""
    lines = [
        "Controls application logging to stderr.",
        "\n",
        "\b\nVerbosity levels:",
        "  0 = Logging disabled (default).",
        *(f"  {verbosity} = {line}" for verbosity, line in enumerate(descriptions, start=1)),
        f"Repeat up to {len(descriptions)} times for increased verbosity.",
    ]
    return "\n".join(lines)
