import pytest as pytest

from rics.translation.offline.parse_format_string import (
    BadDelimiterError,
    Element,
    UnusedOptionalBlockError,
    get_elements,
)


@pytest.mark.parametrize(
    "s, expected",
    [
        (
            "static",
            [
                Element(part="static", placeholders=[], required=True),
            ],
        ),
        (
            "{id}",
            [
                Element(part="{id}", placeholders=["id"], required=True),
            ],
        ),
        (
            "[{optional-id}] \\[literal-angle-brackets\\]",
            [
                Element(part="{optional-id}", placeholders=["optional-id"], required=False),
                Element(part=" [literal-angle-brackets]", placeholders=[], required=True),
            ],
        ),
        (
            "{id} \\[literal-angle-brackets\\]",
            [
                Element(part="{id} [literal-angle-brackets]", placeholders=["id"], required=True),
            ],
        ),
        (
            "!{id}:[:{code}<]:{name}<",
            [
                Element(part="!{id}:", placeholders=["id"], required=True),
                Element(part=":{code}<", placeholders=["code"], required=False),
                Element(part=":{name}<", placeholders=["name"], required=True),
            ],
        ),
        (
            "{id}:{first_name}[ '{nickname}'][, age {age}].",
            [
                Element(part="{id}:{first_name}", placeholders=["id", "first_name"], required=True),
                Element(part=" '{nickname}'", placeholders=["nickname"], required=False),
                Element(part=", age {age}", placeholders=["age"], required=False),
                Element(part=".", placeholders=[], required=True),
            ],
        ),
    ],
)
def test_get_elements(s, expected):
    assert get_elements(s) == expected


@pytest.mark.parametrize(
    "s, i, already_open",
    [
        ("]", 0, False),
        ("[[", 1, True),
        ("[{a}] ]", 6, False),
    ],
)
def test_improper_brackets(s, i, already_open):
    with pytest.raises(BadDelimiterError, match=f"{i=}.*{'' if already_open else ''}"):
        get_elements(s)


def test_unterminated_block():
    with pytest.raises(BadDelimiterError, match="opened at i=2.*never closed"):
        get_elements("  [  ")


def test_optional_block_without_placeholders():
    with pytest.raises(UnusedOptionalBlockError, match="(1, 6)"):
        get_elements(" [aaaa] ")
