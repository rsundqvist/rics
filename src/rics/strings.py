"""String utility methods for Python applications."""


def without_suffix(arg: str, suffix: str) -> str:
    """Remove `suffix` from the tail of `arg`."""
    if not arg.endswith(suffix):
        raise ValueError(f"{arg=} does not end with {suffix=}.")
    return arg[: -len(suffix)]


def without_prefix(arg: str, prefix: str) -> str:
    """Remove `prefix` from the head of `arg`."""
    if not arg.startswith(prefix):
        raise ValueError(f"{arg=} does not start with {prefix=}.")
    return arg[len(prefix) :]
