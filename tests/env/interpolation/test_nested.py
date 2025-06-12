from typing import TypeVar

import pytest

from rics.env.interpolation import UnsetVariableError, Variable
from tests.env.interpolation.conftest import set_variables

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
        ("${ENV_VAR1:${ENV_VAR2}}", "VALUE2"),
        ("${ENV_VAR1:${ENV_VAR1:${ENV_VAR1:default}}}", "default"),
        ("${ENV_VAR1:${ENV_VAR3:${ENV_VAR0}}}", "VALUE0"),
    ],
)
def test_parsing(s, expected):
    set_variables(0, 2, 4)
    actual = Variable.parse_first(s).get_value(resolve_nested_defaults=True)
    assert actual == expected


@pytest.mark.parametrize(
    "s, match",
    [
        ("${ENV_VAR1:use ${ENV_VAR2}}!", "inner match must be stripped"),
        ("${ENV_VAR1:${ENV_VAR2}${ENV_VAR2}}!", "Multiple inner"),
    ],
)
def test_not_implemented(s, match):
    set_variables(2)
    var = Variable.parse_first(s)
    with pytest.raises(NotImplementedError, match=match):
        var.get_value(resolve_nested_defaults=True)


@pytest.mark.parametrize("string", ["${ENV_VAR1:${ENV_VAR3:${ENV_VAR5}}}", "${ENV_VAR1:${ENV_VAR3}}"])
def test_unset(string):
    set_variables(0, 2, 4)
    var = Variable.parse_first(string)

    with pytest.raises(UnsetVariableError, match="Not set."):
        var.get_value(resolve_nested_defaults=True)


def test_python_fstring():
    variables = Variable.parse_string("${ENV_VAR0:tests}{count}{count:.3}{count!r}${ENV_VAR1}")
    assert len(variables) == 2

    actual = variables[0]
    assert actual.name == "ENV_VAR0"
    assert actual.full_match == "${ENV_VAR0:tests}"
    assert actual.default == "tests"

    actual = variables[1]
    assert actual.name == "ENV_VAR1"
    assert actual.full_match == "${ENV_VAR1}"
    assert actual.default is None
