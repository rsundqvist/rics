from rics import strings


def format_perf_counter(start: float, end: float | None = None) -> str:
    """Deprecated alias of :func:`rics.strings.format_perf_counter`."""
    _warn("format_perf_counter")
    return strings.format_perf_counter(start, end=end, full=True)


def format_seconds(t: float, *, allow_negative: bool = False) -> str:
    """Deprecated alias of :func:`rics.strings.format_seconds`."""
    _warn("format_seconds")
    return strings.format_seconds(t, allow_negative=allow_negative, full=True)


def _warn(name: str) -> None:
    import warnings

    msg = (
        f"Function `rics.performance.{name}()` is deprecated."
        f"\nUse `rics.strings.{name}()` instead, or pin `rics==4.0.1` to hide this warning."
    )
    warnings.warn(msg, category=DeprecationWarning, stacklevel=3)
