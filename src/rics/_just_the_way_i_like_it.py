from typing import Any

_SKIP_WARNING: bool = False


def configure_stuff(
    level: int | str = "INFO",
    rics_level: int | str = "INFO",
    id_translation_level: int | str = "INFO",
    matplotlib_level: int | str = "WARNING",
    logging: bool = True,
    pandas: bool = True,
    plotting: bool = True,
    ghost: bool = True,
    **kwargs: Any,
) -> None:
    """Configure a bunch of stuff to match my personal preferences. May do strange stuff 👻.

    .. warning::

       This function can and will change without warning, and will not be documented in the changelog. Don't use for
       anything important.

    Set :envvar:`JTWILI=true <JTWILI>` to disable the warning.

    Args:
        level: Log level for the root logger. Default is ``logging.INFO``.
        rics_level: Log level for the :mod:`rics` package. Default is ``logging.INFO``.
        id_translation_level: Log level for the :mod:`id_translation` package. Default is ``logging.INFO``.
        matplotlib_level: Log level for the :mod:`matplotlib` package. Default is ``logging.WARNING``.
        logging: If ``True``, attempt to perform logging configuration.
        pandas: If ``True``, attempt to perform pandas configuration.
        plotting: If ``True``, attempt to perform plotting (e.g. matplotlib) configuration.
        ghost: Set to ``False`` to disable `'👻 Configured some stuff just the way I like it!'`.
        **kwargs: Keyword arguments for :func:`rics.logs.basic_config` and :py:func:`logging.basicConfig`.

    """
    import contextlib

    if logging:
        from .logs import basic_config

        basic_config(
            level=level,
            rics_level=rics_level,
            id_translation_level=id_translation_level,
            matplotlib_level=matplotlib_level,
            **kwargs,
        )

    if pandas:
        _configure_pandas()

    if plotting:
        with contextlib.suppress(ModuleNotFoundError):
            from .plotting import configure

            configure()

    if ghost:
        print("👻 Configured some stuff just the way I like it!")
    _maybe_emit_warning()


def _configure_pandas() -> None:
    try:
        import pandas as pd
    except ModuleNotFoundError:
        return

    import contextlib

    pd.options.display.max_columns = 50
    pd.options.display.max_colwidth = 150
    pd.options.display.max_rows = 250
    pd.options.display.width = 0
    pd.options.display.float_format = "{:.6g}".format

    pd.options.mode.chained_assignment = "raise"
    if hasattr(pd.options.mode, "copy_on_write") and pd.options.mode.copy_on_write is None:
        pd.options.mode.copy_on_write = "warn"

    with contextlib.suppress(ImportError):
        pd.plotting.register_matplotlib_converters()


def _maybe_emit_warning() -> None:  # pragma: no cover
    import logging
    import os
    import sys
    import traceback
    from multiprocessing import process

    global _SKIP_WARNING  # noqa: PLW0603
    if _SKIP_WARNING:
        return
    _SKIP_WARNING = True

    if os.environ.get("JTWILI", "").lower() == "true":
        return

    if getattr(process.current_process(), "_inheriting", False):
        return  # From multiprocessing.spawn._check_not_importing_main

    try:
        get_ipython()  # type: ignore[name-defined]
        return  # noqa: TRY300 # Typically in a console or notebook
    except NameError:
        pass

    caller = traceback.format_stack()[-3]
    message = f"If you're seeing this in bad places, remove the call to rics.configure_stuff() in:\n{caller}"

    logger = logging.getLogger("rics")
    if logger.isEnabledFor(logging.WARNING):
        logger.warning(message)
    else:
        print(message, end="", file=sys.stderr)
