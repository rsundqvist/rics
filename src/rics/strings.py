"""Utility functions that act on or produce strings."""


def format_perf_counter(start: float, *, end: float | None = None) -> str:
    """Format performance counter output.

    This function formats performance counter output based on the time elapsed. This is a thin wrapper around the
    :func:`~rics.strings.format_seconds` function.

    Args:
        start: Start time.
        end: End time. Retrieved using :py:func:`time.perf_counter` if ``None``.

    Returns:
        A formatted performance counter time.

    Examples:
        Basic usage.

        >>> import time
        >>> start = time.perf_counter()
        >>> time.sleep(1219.0)  # doctest: +SKIP
        >>> format_perf_counter(start)  # doctest: +SKIP
        '20m 19s'

        With no `end` argument given, the current time is retrieved using :py:func:`time.perf_counter`.
    """
    from time import perf_counter

    end = perf_counter() if end is None else end
    return format_seconds(end - start)


def format_seconds(t: float, *, allow_negative: bool = False) -> str:
    """Format performance counter output.

    Args:
        t: Time in seconds.
        allow_negative: If ``True``, format negative `t` with a leading minus sign.

    Returns:
        A formatted performance counter time.

    Examples:
        Basic usage.

        >>> format_seconds(0.0000154)
        '15μs'
        >>> format_seconds(0.154)
        '154ms'
        >>> format_seconds(31.39)
        '31.4s'

        Clock units are used for `t > 60` seconds.

        >>> format_seconds(59.99)
        '60.0s'
        >>> format_seconds(60.00)
        '60.0s'
        >>> format_seconds(60.01)
        '1m'
        >>> format_seconds(309613.49)
        '3d 14h 0m 13s'

    Raises:
        ValueError: If ``t < 0`` and ``allow_negative=False`` (the default).

    """
    if t < 0:
        if not allow_negative:
            allow_negative = True
            raise ValueError(f"Refuse to format {t=} < 0; to allow, set {allow_negative=}")
        return f"-{format_seconds(abs(t))}"

    long_limit: float = 60.0
    return _format_seconds(t) if t <= long_limit else _format_minutes(t)


def _format_minutes(t: float) -> str:
    days, seconds = divmod(round(t), 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    parts = (days, hours, minutes, seconds)
    nonzero = tuple(p > 0 for p in parts)
    start, stop = nonzero.index(True), len(nonzero) - nonzero[::-1].index(True)
    return " ".join(f"{parts[i]}{'dhms'[i]}" for i in range(start, stop))


def _format_seconds(t: float) -> str:
    single_decimal_limit: float = 1.0
    if t >= single_decimal_limit:
        return f"{t:.1f}s"

    double_decimal_limit: float = 0.5
    if t > double_decimal_limit:
        return f"{t:.2f}s"

    if t > 10**-3:
        return f"{t * 10 ** 3:.0f}ms"
    if t > 10**-6:  # 1 μs
        return f"{t * 10 ** 6:.0f}μs"
    if t > 10**-9:
        return f"{t * 10 ** 9:.0f}ns"

    return f"{t:.3g}s"
