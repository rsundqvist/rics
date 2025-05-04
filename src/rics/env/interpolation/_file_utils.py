from ._variable import UnsetVariableError, Variable


def replace_in_string(
    s: str,
    *,
    allow_nested: bool = True,
    allow_blank: bool = False,
) -> str:
    """Interpolate environment variables in a string `s`.

    This function replaces references to environment variables with the actual value of the variable, or a default if
    specified. The syntax is similar to Bash string interpolation; use ``${<var>}`` for mandatory variables, and
    ``${<var>:default}`` for optional variables.

    Args:
        s: A string in which to interpolate.
        allow_blank: If ``True``, allow variables to be set but empty.
        allow_nested: If ``True`` allow using another environment variable as the default value. This option will not
            verify whether the actual values are interpolation-strings.

    Returns:
        A copy of `s`, after environment variable interpolation.

    Raises:
        ValueError: If nested variables are discovered (only when ``allow_nested=False``).
        UnsetVariableError: If any required environment variables are unset or blank (only when ``allow_blank=False``).
    """
    for var in Variable.parse_string(s):
        if not allow_nested and (var.default and Variable.parse_string(var.default)):
            raise ValueError(f"Nested variables forbidden since {allow_nested=}.")

        value = var.get_value(resolve_nested_defaults=allow_nested).strip()

        if not (allow_blank or value):
            msg = f"Empty values forbidden since {allow_blank=}."
            raise UnsetVariableError(var.name, msg)

        s = s.replace(var.full_match, value)
    return s
