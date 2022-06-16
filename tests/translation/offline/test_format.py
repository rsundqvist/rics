import pytest as pytest

from rics.translation.offline import Format


@pytest.fixture(scope="module")
def fmt():
    yield Format("{id}:[:{code}:]{name}")


@pytest.mark.parametrize(
    "fmt, expected_parts",
    [
        ("!{id}:[:{code}<]:{name}<", ["!", "{id}", ":", ":{code}<", ":", "{name}", "<"]),
        ("!{id}:[:{code}<][:{name}<]<", ["!", "{id}", ":", ":{code}<", ":{name}<", "<"]),
        ("!><{id}:[:{code}<][:{name}]", ["!><", "{id}", ":", ":{code}<", ":{name}"]),
        ("{id}:[:{code}]:{name}", ["{id}", ":", ":{code}", ":", "{name}"]),
    ],
)
def test_parse(fmt, expected_parts):
    parts = [e.part for e in Format._parse_format_string(fmt)]
    assert parts == expected_parts


@pytest.mark.parametrize(
    "placeholders, expected",
    [
        (("id", "code", "name"), "{id}::{code}:{name}"),
        (("id", "name"), "{id}:{name}"),
    ],
)
def test_for_placeholders(fmt, placeholders, expected):
    assert fmt.fstring(placeholders) == expected


@pytest.mark.parametrize(
    "translations, expected",
    [
        ({"id": 1, "code": "SE", "name": "Sweden"}, "1::SE:Sweden"),
        ({"id": 1, "name": "Sweden"}, "1:Sweden"),
    ],
)
def test_format(fmt, translations, expected):
    assert fmt.fstring(translations).format(**translations) == expected


def test_missing_required(fmt):
    with pytest.raises(KeyError):
        fmt.fstring(("does", "not", "exist"))


@pytest.mark.xfail
@pytest.mark.parametrize(
    "kwargs, expected",
    [
        ({"id": "my-id"}, "{my-id} is required"),
        ({"id": "my-id", "optional": "my-optional"}, "{my-id} is required, 'my-optional' is [optional]!"),
    ],
)
def test_nested(kwargs, expected):
    fmt = Format("{{{id}}} is required[, '{optional}' is [optional]!]")
    fstring = fmt.fstring(kwargs)
    assert fstring.format(**kwargs) == expected
