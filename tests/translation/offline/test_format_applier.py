import pytest

from rics.translation.offline import Format, TranslationMap
from rics.translation.offline.types import PlaceholderTranslations


@pytest.fixture(scope="module")
def fmt():
    return Format("{foo} {id}[: baz={baz}]")


def test_missing_default_placeholder():
    translations = PlaceholderTranslations("source", ("id", "baz"), [(1, 1), (2, 2)], 0)

    with pytest.raises(ValueError):
        TranslationMap.FORMAT_APPLIER_TYPE(translations, default={"bar": "default"})


def test_no_explicit_placeholders(fmt):
    translations = PlaceholderTranslations("source", ("id", "baz", "foo"), [(1, 1, 3), (2, 2, 4)], 0)
    applier = TranslationMap.FORMAT_APPLIER_TYPE(translations)

    ans = applier(fmt)
    assert ans == {1: "3 1: baz=1", 2: "4 2: baz=2"}


def test_explicit_placeholders(fmt):
    translations = PlaceholderTranslations("source", ("id", "baz", "foo"), [(1, 1, 3), (2, 2, 4)], 0)
    applier = TranslationMap.FORMAT_APPLIER_TYPE(translations, {"baz": "default-baz", "foo": "default-baz"})

    ans = applier(fmt, ("foo", "id"))
    assert ans == {1: "3 1", 2: "4 2"}
