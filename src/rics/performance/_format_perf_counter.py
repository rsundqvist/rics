from time import perf_counter


def format_perf_counter(start: float, end: float = None) -> str:
    """Format performance counter output.

    This function formats performance counter output based on the time elapsed. For ``t < 120 sec``, accuracy is
    increased whereas for durations above one minute a more user-friendly formatting is used.

    Args:
        start: Start time.
        end: End time. Set to now if not given.

    Returns:
        A formatted performance counter time.

    Examples:
        >>> from rics.performance import format_perf_counter
        >>> format_perf_counter(0, 313113.31)
        '3d 14h 59m'
        >>> format_perf_counter(0, 0.154)
        '154ms'
        >>> format_perf_counter(0, 31.39)
        '31.4s'

    See Also:
        :py:func:`time.perf_counter`
    """
    t = (end or perf_counter()) - start
    return format_seconds(t)


def format_seconds(t: float, allow_negative: bool = False) -> str:
    """Format performance counter output.

    This function formats performance counter output based on the time elapsed. For ``t < 120 sec``, accuracy is
    increased whereas for durations above one minute a more user-friendly formatting is used.

    Args:
        t: Time in seconds.
        allow_negative: If ``True``, format negative `t` with a leading minus sign.

    Returns:
        A formatted performance counter time.

    Raises:
        ValueError: If ``t < 0`` and ``allow_negative=False`` (the default).
    """
    if t < 0:
        if not allow_negative:
            allow_negative = True
            raise ValueError(f"Refuse to format {t=} < 0; to allow, set {allow_negative=}")
        return f"-{format_seconds(abs(t))}"

    if t > 60.0:
        days, seconds = divmod(t, 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)

        if days:
            return f"{days:.0f}d {hours:.0f}h {minutes + seconds / 60:.0f}m"
        elif hours:
            return f"{hours:.0f}h {minutes:.0f}m {seconds:.0f}s"
        else:
            return f"{minutes:.0f}m {seconds:.0f}s"

    if t >= 1.0:
        return f"{t:.1f}s"
    if t > 0.5:
        return f"{t:.2f}s"
    if t > 10**-3:
        return f"{t * 10 ** 3:.0f}ms"
    if t > 10**-6:  # 1 μs
        return f"{t * 10 ** 6:.0f}μs"
    if t > 10**-9:
        return f"{t * 10 ** 9:.0f}ns"

    return f"{t:.3g}s"
