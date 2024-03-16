import pytest
from rics.envinterp import UnsetVariableError, Variable

from tests.envinterp.conftest import set_variables

VARIABLES = [
    Variable("ENV_VAR0", None, "${ENV_VAR0}"),
    Variable("ENV_VAR0", None, "${  ENV_VAR0  }"),
    Variable("ENV_VAR1", "", "${ENV_VAR1:}"),
    Variable("ENV_VAR2", "default", "${ENV_VAR2:default}"),
    Variable("ENV_VAR2", "${NESTED}", "${ENV_VAR2:${NESTED}}"),
]

for v in VARIABLES:
    print(v.full_match)


@pytest.mark.parametrize("expected", VARIABLES)
def test_parsing(expected):
    print(expected.full_match)
    actual = Variable.parse_first(expected.full_match)
    assert actual == expected


@pytest.mark.parametrize("var", VARIABLES)
def test_value_is_unset(var):
    set_variables()
    variable = Variable.parse_first(var.full_match)

    if variable.is_optional:
        assert variable.get_value() == variable.default
        return

    with pytest.raises(UnsetVariableError):
        variable.get_value()


def test_value_is_set():
    expected = set_variables(*range(10))
    for var in VARIABLES:
        assert var.get_value() == expected[var.name]
