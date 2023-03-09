from ._variable import Variable


def replace_in_string(s: str) -> str:
    """Replace environment variable names with their values in `s`.

    Recursive variable interpolation is not supported by this function.

    Args:
        s: A string.

    Returns:
        A copy of `s` with the env vars names found within their values.

    Raises:
        UnsetVariableError: If any variables are unset with no default specified.
    """
    for var in Variable.parse_string(s):
        s = s.replace(var.full_match, var.get_value())
    return s
