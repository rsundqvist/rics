import pytest

from rics._internal_support.types import NO_DEFAULT
from rics.translation.offline import MagicDict

FSTRING = "My name is {} and my number is {}."
PLACEHOLDERS = ("name", "id")

REAL_TRANSLATIONS = {
    1991: "My name is Richard and my number is 1991.",
    1999: "My name is Sofia and my number is 1999.",
}


@pytest.mark.parametrize(
    "default_value, id_in_placeholders, expected",
    [
        ("[UNKNOWN NAME]", True, "My name is [UNKNOWN NAME] and my number is -1."),
        ("[UNKNOWN NAME]", False, "My name is [UNKNOWN NAME]."),
    ],
)
def test_with_default(default_value, id_in_placeholders, expected):
    subject = make_with_default(default_value, id_in_placeholders)

    assert -1 in subject
    assert -321321 in subject
    # Get
    assert subject.get(1991, "get-default") == "My name is Richard and my number is 1991."
    assert subject.get(1999, "get-default") == "My name is Sofia and my number is 1999."
    assert subject.get(-1, "get-default") == expected
    # Getitem
    assert subject[1991] == "My name is Richard and my number is 1991."
    assert subject[1999] == "My name is Sofia and my number is 1999."
    assert subject[-1] == expected


def test_no_default():
    subject = MagicDict.make(REAL_TRANSLATIONS, FSTRING, PLACEHOLDERS)

    assert -1 not in subject
    assert -321321 not in subject
    # Get
    assert subject.get(1991, "get-default") == "My name is Richard and my number is 1991."
    assert subject.get(1999, "get-default") == "My name is Sofia and my number is 1999."
    assert subject.get(-1, "get-default") == "get-default"
    # Getitem
    assert subject[1991] == "My name is Richard and my number is 1991."
    assert subject[1999] == "My name is Sofia and my number is 1999."
    with pytest.raises(KeyError):
        subject[-1]


def make_with_default(default_value, id_in_placeholders) -> MagicDict:
    return MagicDict.make(
        REAL_TRANSLATIONS,
        FSTRING if id_in_placeholders else "My name is {}.",
        PLACEHOLDERS if id_in_placeholders else ("name",),
        {"name": default_value} if default_value else NO_DEFAULT,
    )
