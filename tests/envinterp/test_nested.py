from typing import TypeVar, Union

import pytest

from rics.envinterp import UnsetVariableError, Variable
from tests.envinterp.conftest import set_variables

ExcType = TypeVar("ExcType", bound=Exception)

VARIABLES = [
    Variable("ENV_VAR0", None, "${ENV_VAR0}"),
    Variable("ENV_VAR1", "", "${ENV_VAR1:}"),
    Variable("ENV_VAR2", "default", "${ENV_VAR2:default}"),
    Variable("ENV_VAR2", "${NESTED}", "${ENV_VAR2:${NESTED}}"),
]


@pytest.mark.parametrize(
    "s, expected",
    [
        ("${ENV_VAR0:{ENV_VAR2}", "VALUE0"),
        ("${ENV_VAR1:${ENV_VAR2}}", "VALUE2"),
        ("${ENV_VAR1:${ENV_VAR1:${ENV_VAR1:default}}}", "default"),
        ("${ENV_VAR1:${ENV_VAR3:${ENV_VAR5}}}", UnsetVariableError),
        ("${ENV_VAR1:${ENV_VAR3:${ENV_VAR0}}}", "VALUE0"),
        ("${ENV_VAR1:${ENV_VAR3}}", UnsetVariableError),
        ("${ENV_VAR1:use ${ENV_VAR2}}!", NotImplementedError),
        ("${ENV_VAR1:${ENV_VAR2}${ENV_VAR2}}!", NotImplementedError),
    ],
)
def test_parsing(s, expected):
    set_variables(0, 2, 4)
    actual = get_value_exception(Variable.parse_first(s))
    if isinstance(actual, str):
        assert actual == expected
    else:
        assert isinstance(actual, expected)


def get_value_exception(var: Variable) -> Union[str, Exception]:
    try:
        return var.get_value(resolve_nested_defaults=True)
    except Exception as e:  # noqa: B902
        return e
