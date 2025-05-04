"""Environment variable interpolation in files and strings.

This module provides utilities to read text and replace environment variable references with the actual environment
variable value using a familiar syntax. Optional default values are also possible, as well as recursively nested
variables (must be explicitly enabled).

Syntax:
    Similar to Bash variable interpolation; ``${<var>}``, where ``<var>`` is the name of the environment variable you
    wish to extract. This particular form will raise an exception if ``<var>`` is not set.

Default values:
    Default values are specified by stating the default value after a colon; ``${<var>:default-value}``. The default
    value may be blank, in which case an empty string is used as the default.

There are three main ways of using this module:

    * The :meth:`.Variable.parse_string`-function, combined with :meth:`.Variable.get_value`. This gives you the most
      amount of control.
    * The :func:`replace_in_string`-function, for basic interpolation without recursion in an entire string.
    * The :func:`rics.misc.interpolate_environment_variables`-function, which adds some additional logic on top of what
      the :class:`Variable`-methods provide.

Examples:
    We'll set ``ENV_VAR0=VALUE0`` and ``ENV_VAR1=VALUE1``. Vars 2 and 4 are not set.

    >>> from os import environ
    >>> environ["ENV_VAR0"] = "VALUE0"
    >>> environ["ENV_VAR1"] = "VALUE1"

    Basic interpolation.

    >>> Variable.parse_first("${ENV_VAR0}").get_value()
    'VALUE0'

    Setting a default works as expected. The default may also be empty.

    >>> Variable.parse_first("${ENV_VAR2:default}").get_value()
    'default'
    >>> Variable.parse_first("${ENV_VAR2:}").get_value()
    ''

    The variable must exist if no default is given.

    >>> Variable.parse_first("${DOESNT_EXIST}").get_value()  # doctest: +SKIP
    UnsetVariableError: Required Environment Variable 'DOESNT_EXIST': Not set.

    Furthermore, variables may be nested, but this requires setting the flag to enable recursive parsing.

    >>> Variable.parse_first("${ ENV_VAR2 :${ ENV_VAR0 }}").get_value(
    ...     resolve_nested_defaults=True
    ... )
    'VALUE0'

    Whitespaces around the names is fine. Finally, nesting may be arbitrarily deep.

    >>> Variable.parse_first("${ENV_VAR3:${ENV_VAR4:${ENV_VAR0}}}").get_value(True)
    'VALUE0'

    TODO infinite recursion ovan?
"""

from ._file_utils import replace_in_string
from ._variable import UnsetVariableError, Variable

__all__ = ["UnsetVariableError", "Variable", "replace_in_string"]
