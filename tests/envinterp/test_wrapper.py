import os

import pytest

from rics import misc
from rics.envinterp import UnsetVariableError


@pytest.mark.parametrize(
    "s, expected",
    [
        ("", ""),
        ("no vars!", "no vars!"),
        (
            "${ ENV_VAR0 \t} exists, but ${  ENV_VAR100  :not this} one",
            "VALUE0 exists, but not this one",
        ),
    ],
)
def test_interpolate_environment_variables_default_args(s, expected):
    os.environ["ENV_VAR0"] = "VALUE0"
    os.environ["ENV_VAR1"] = "VALUE1"
    assert misc.interpolate_environment_variables(s) == expected


@pytest.mark.parametrize(
    "s, expected, kwargs",
    [
        ("${ENV_VAR0:${ENV_VAR0}}", ValueError, dict(allow_nested=False)),
        ("${HACKY}", "${NESTED}", dict(allow_nested=False)),
        ("${NOT_SET:}", UnsetVariableError, dict(allow_blank=False)),
        ("${BLANK}", "", dict(allow_blank=True)),
        ("${BLANK}", UnsetVariableError, dict(allow_blank=False)),
        ("${BLANK:${ BLANK }}", UnsetVariableError, dict()),
        ("${BLANK:${ NOT_SET }}", UnsetVariableError, dict()),
    ],
)
def test_interpolate_environment_variables(s, expected, kwargs):
    os.environ["ENV_VAR0"] = "VALUE0"
    os.environ["BLANK"] = " "
    os.environ["HACKY"] = "${NESTED}"

    try:
        actual = misc.interpolate_environment_variables(s, **kwargs)
    except (ValueError, UnsetVariableError, NotImplementedError) as e:
        actual = e  # type: ignore

    if isinstance(actual, str):
        assert actual == expected
        return

    assert isinstance(actual, expected)
