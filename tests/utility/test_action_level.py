from typing import Any

import pytest

from rics.utility.action_level import ActionLevel, ActionLevelHelper, BadActionLevelError


def run(func, expected, action, purpose, *args: Any) -> None:
    if expected is None:
        with pytest.raises(BadActionLevelError) as rc:
            func(action, purpose, *args)
        assert purpose in str(rc.value)
    else:
        actual = func(action, purpose, *args)
        assert isinstance(actual, ActionLevel)
        assert actual is expected


@pytest.mark.parametrize(
    "action, expected",
    [
        (ActionLevel.IGNORE, ActionLevel.IGNORE),
        (ActionLevel.IGNORE.value, ActionLevel.IGNORE),
        (ActionLevel.IGNORE.name, ActionLevel.IGNORE),
        ("ignored", None),
        (0, None),
    ],
)
def test_verify(action, expected):
    purpose = "Testing stuff!"
    forbidden = None
    run(ActionLevel.verify, expected, action, purpose, forbidden)


@pytest.mark.parametrize(
    "action, purpose, expected",
    [
        (ActionLevel.IGNORE, None, ActionLevel.IGNORE),
        (ActionLevel.IGNORE.value, "all-allowed", ActionLevel.IGNORE),
        (ActionLevel.IGNORE, "no-ignore-0", None),
        (ActionLevel.IGNORE, "no-ignore-1", None),
        (ActionLevel.WARN, "no-ignore-1", ActionLevel.WARN),
    ],
)
def test_helper_verify(action, purpose, expected, helper):
    run(helper.verify, expected, action, purpose)


def test_no_purpose():
    with pytest.raises(ValueError) as ec:
        ActionLevelHelper().verify(ActionLevel.IGNORE, "not-known")

    assert ec.value.args == ("Unknown purpose='not-known' given.",)


@pytest.fixture
def helper():
    return ActionLevelHelper(
        require_purpose="given",
        **{
            "all-allowed": None,
            "no-ignore-0": "ignore",
            "no-ignore-1": ActionLevel.IGNORE,
        },
    )
