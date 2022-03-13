from datetime import timedelta
from time import perf_counter


def format_perf_counter(start: float, end: float = None) -> str:
    """Format performance counter output.

    This function formats performance counter output based on the time elapsed. For ``t < 60 sec``, accuracy is
    increased whereas for durations above one minute a more user-friendly formatting is used.

    Args:
        start: Start time.
        end: End time. Set to now if not given.

    Returns:
        A formatted performance counter time.

    Examples:
        >>> from rics.utility.perf import format_perf_counter
        >>> format_perf_counter(0, 3131)  # 3131 seconds is about 52 minutes.
        '0:52:11'
        >>> format_perf_counter(0, 0.154)
        '0.154 sec'

    See Also:
        :py:func:`time.perf_counter`
    """
    t = (end or perf_counter()) - start
    if t < 1.0:
        return f"{t:.6g} sec"
    if t < 60.0:
        return f"{t:.2f} sec"
    else:
        return str(timedelta(seconds=round(t)))
