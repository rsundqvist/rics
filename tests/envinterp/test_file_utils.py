import pytest

from rics.envinterp import replace_in_string
from tests.envinterp.conftest import set_variables


@pytest.fixture(scope="session")
def expected():
    yield """
        k0 = "${ENV_VAR0}"                  # If ENV_VAR0 does not exist, crash.
        k1 = "${ENV_VAR1:}"                 # If ENV_VAR1 does not exist, delete the 'k1'-key.
        k2 = "${ENV_VAR2:default}"          # If ENV_VAR2 does not exist, replace it with 'default'
        k3 = "${ENV_VAR3?bad-syntax!}"
    """


def test_all_set(expected):
    set_variables(0, 1, 2, 3)

    actual = replace_in_string(expected)
    assert (
        actual
        == """
        k0 = "VALUE0"                  # If ENV_VAR0 does not exist, crash.
        k1 = "VALUE1"                 # If ENV_VAR1 does not exist, delete the 'k1'-key.
        k2 = "VALUE2"          # If ENV_VAR2 does not exist, replace it with 'default'
        k3 = "${ENV_VAR3?bad-syntax!}"
    """
    )


def test_required_set(expected):
    set_variables(0, 3)

    actual = replace_in_string(expected)
    assert (
        actual
        == """
        k0 = "VALUE0"                  # If ENV_VAR0 does not exist, crash.
        k1 = ""                 # If ENV_VAR1 does not exist, delete the 'k1'-key.
        k2 = "default"          # If ENV_VAR2 does not exist, replace it with 'default'
        k3 = "${ENV_VAR3?bad-syntax!}"
    """
    )
