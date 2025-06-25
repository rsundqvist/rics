"""Utility functions that act on or produce strings."""


def format_bytes(n: int, *, binary: bool = True, long: bool = False, decimals: int = 2) -> str:
    """Format bytes as a string.

    Args:
        n: Number of bytes. Must be positive.
        binary: Output `binary <https://en.wikipedia.org/wiki/Binary_prefix>`_ prefixes if ``True``,
            use `metric (SI) <https://en.wikipedia.org/wiki/Metric_prefix>`_ prefixes otherwise.
        long: Output out full unit and prefix if ``True``, use abbreviated versions otherwise.
        decimals: Number of decimals to include. Ignored for when `n < base`.

    Returns:
        Formatted number of bytes.

    Examples:
        **Formatting on prefix bounds**

        The jump as made at `base / 2`, where `base` is one of 1024 and 1000 (when ``binary=False``).

        >>> format_bytes(512 * 1024)
        '512.00 KiB'
        >>> format_bytes(512 * 1024 + 1)
        '0.50 MiB'

        This rule does *not* apply when `n <= base`.

        >>> format_bytes(1024, long=True)
        1024 bytes
        >>> format_bytes(1024 + 1)
        '1.00 KiB'

        **Output flags**

        >>> format_bytes(20190511, binary=False, long=False)
        '20.19 MB'
        >>> format_bytes(20190511, binary=False, long=True)
        '20.19 megabytes'
        >>> format_bytes(20190511, binary=True, long=False)
        '19.26 MiB'
        >>> format_bytes(20190511, binary=True, long=True)
        '19.26 mebibytes'

        **Large outputs**

        Metric and binary have different upper limits.

        >>> format_bytes(21**21, binary=True)
        '2416.44 YiB'
        >>> format_bytes(21**21, binary=True, long=True)
        '2416.44 yobibytes'
        >>> format_bytes(21**21, binary=False)
        '5.84 RB'
        >>> format_bytes(21**21, binary=False, long=True)
        '5.84 ronnabytes'

        If you ever see output like this, please let me know so that I can brag that someone important is using my
        little library.
    """
    base = 1024 if binary else 1000

    if n <= base:
        return f"{n} {'bytes' if long else 'B'}"

    x: float = n * 2.0
    n_divisions = -1
    while x > base:
        x /= base
        n_divisions += 1

    if binary:
        # https://en.wikipedia.org/wiki/Binary_prefix
        if long:
            prefixes = ["kibi", "mebi", "gibi", "tebi", "pebi", "exbi", "zebi", "yobi"]
        else:
            prefixes = ["Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi", "Yi"]
    else:  # noqa: PLR5501  # BUG: this rule doesn't preserve comments: https://github.com/astral-sh/ruff/issues/9790
        # https://en.wikipedia.org/wiki/Metric_prefix
        if long:
            prefixes = ["kilo", "mega", "giga", "tera", "peta", "exa", "zetta", "yotta", "ronna", "quetta"]
        else:
            prefixes = ["k", "M", "G", "T", "P", "E", "Z", "Y", "R", "Q"]

    try:
        prefix = prefixes[n_divisions]
    except IndexError:
        prefix = prefixes[-1]
        x = n / base ** len(prefixes)

    prefix += "bytes" if long else "B"
    return f"{x / 2:.{decimals}f} {prefix}"


def format_perf_counter(start: float, *, end: float | None = None, full: bool = False) -> str:
    """Format performance counter output.

    This function formats performance counter output based on the time elapsed. This is a thin wrapper around the
    :func:`~rics.strings.format_seconds` function.

    Args:
        start: Start time.
        end: End time. Retrieved using :py:func:`time.perf_counter` if ``None``.
        full: If ``True``, show all non-zero components above four hours.

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
    return format_seconds(end - start, full=full)


def format_seconds(t: float, *, allow_negative: bool = False, full: bool = False) -> str:
    """Format performance counter output.

    Args:
        t: Time in seconds.
        allow_negative: If ``True``, format negative `t` with a leading minus sign.
        full: If ``True``, show all non-zero components above four hours.

    Returns:
        A formatted performance counter time.

    Examples:
        Basic usage.

        >>> format_seconds(0.0000154)
        '15 μs'
        >>> format_seconds(0.154)
        '154 ms'
        >>> format_seconds(31.39)
        '31.4 sec'

        Clock units are used for `t > 60` seconds.

        >>> format_seconds(59.99)
        '60.0 sec'
        >>> format_seconds(60.00)
        '60.0 sec'
        >>> format_seconds(60.01)
        '1m'
        >>> format_seconds(309623.49)
        '3d 14h'

        Large intervals is rounded by default. You may set ``full=True`` to show full output.

        >>> format_seconds(309623.49)
        '3d 14h'
        >>> format_seconds(309633.51, full=True)
        '3d 14h 0m 34s'

    Raises:
        ValueError: If ``t < 0`` and ``allow_negative=False`` (the default).

    """
    if t < 0:
        if not allow_negative:
            allow_negative = True
            raise ValueError(f"Refuse to format {t=} < 0; to allow, set {allow_negative=}")
        return f"-{format_seconds(abs(t), full=full)}"

    long_limit: float = 60.0
    return _format_seconds(t) if t <= long_limit else _format_minutes(t, full)


def _format_minutes(t: float, full: bool) -> str:
    if full or t < 4 * 3600.0:
        total_seconds = round(t)
    else:
        total_seconds = 60 * round(t / 60)  # Drop seconds above four hours

    days, seconds = divmod(total_seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    parts = (days, hours, minutes, seconds)
    nonzero = tuple(p > 0 for p in parts)
    start = nonzero.index(True)
    stop = len(nonzero) - nonzero[::-1].index(True)
    return " ".join(f"{parts[i]}{'dhms'[i]}" for i in range(start, stop))


def _format_seconds(t: float) -> str:
    single_decimal_limit: float = 1.0
    if t >= single_decimal_limit:
        return f"{t:.1f} sec"

    double_decimal_limit: float = 0.5
    if t > double_decimal_limit:
        return f"{t:.2f} sec"

    if t > 10**-3:
        return f"{t * 10**3:.0f} ms"
    if t > 10**-6:  # 1 μs
        return f"{t * 10**6:.0f} μs"
    if t > 10**-9:
        return f"{t * 10**9:.0f} ns"

    return f"{t:.3g} sec"


def camel_to_snake(s: str) -> str:
    """Naive ``camelCase`` or ``PascalCase`` to ``snake_case`` conversion.

    Args:
        s: A string to convert.

    Returns:
        A ``snake_case`` string.

    Raises:
        IndexError: If `string` is empty.

    Examples:
        Converting camel case strings.

        >>> camel_to_snake("ClassName")
        'class_name'
        >>> camel_to_snake("variableName")
        'variable_name'

        Proper ``snake_case`` strings will not be changed.

        >>> camel_to_snake("already_snake_case")
        'already_snake_case'

    Notes:
        Passing ``SCREAMING_SNAKE_CASE`` strings is **not** supported.
    """
    parts = [s[0]]

    for ch in s[1:]:
        if ch.isupper():
            parts.append("_")
        parts.append(ch)

    return "".join(parts).lower()


def snake_to_camel(s: str, *, lower: bool = True) -> str:
    """Naive ``snake_case`` to ``camelCase`` conversion.

    Args:
        s: A string to convert.
        lower: If ``False``, return ``PamelCase`` instead of ``camelCase``.

    Returns:
        A ``camelCase`` string.

    Raises:
        IndexError: If `string` is empty.

    Examples:
        Converting snake case strings.

        >>> snake_to_camel("snake_case")
        'snakeCase'

        Passing ``SCREAMING_SNAKE_CASE`` strings is supported.

        >>> snake_to_camel("SCREAMING_SNAKE_CASE")
        'screamingSnakeCase'

        Set ``lower=False`` to convert to ``PascalCase`` or ``UpperCamelCase``.

        >>> snake_to_camel("SCREAMING_SNAKE_CASE", lower=False)
        'ScreamingSnakeCase'

    Notes:
        Passing ``camelCase`` strings is **not** supported.
    """
    s = s.title().replace("_", "")
    s0 = s[0]
    if lower:
        s0 = s0.lower()
    return s0 + s[1:]


TRUE = "1", "true", "yes", "on", "enable", "enabled"
FALSE = "0", "false", "no", "off", "disable", "disabled"


def str_as_bool(s: str) -> bool:
    """Convert a string `s` to a boolean value.

    The output is determined by the content of `s`, as per the mapping shown below.

    Keys:
        * False: ``{false}``
        * True: ``{true}``

    Matching is case-insensitive.

    Args:
        s: A string.

    Returns:
        A ``bool`` value.

    Raises:
        TypeError: If `s` is not a string.
        ValueError: If `s` cannot be converted to ``bool`` using the keys above.

    Examples:
        Basic usage.

        >>> str_as_bool("true"), str_as_bool("false")
        (True, False)

        The input is cleaned and normalized.

        >>> str_as_bool(" TRUE"), str_as_bool("False")
        (True, False)

        Input strings are normalized using :py:meth:`str.strip` and :py:meth:`str.lower`.

    Notes:
        Using ``bool(<str>)`` is equivalent to ``len(<str>) == 0``.
    """
    if not isinstance(s, str):
        msg = f"Input must be a string; got {type(s).__name__}."
        raise TypeError(msg)

    s = s.strip().lower()
    if s in FALSE:
        return False
    if s in TRUE:
        return True

    error = ValueError(f"Cannot cast {s!r} to `bool`.")
    error.add_note(f"{FALSE=}")
    error.add_note(f"{TRUE=}")
    raise error


if str_as_bool.__doc__:
    str_as_bool.__doc__ = str_as_bool.__doc__.format(false=FALSE, true=TRUE)
