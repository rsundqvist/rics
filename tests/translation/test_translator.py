import pytest

from rics.mapping.exceptions import MappingError
from rics.translation import Translator
from rics.translation.dio.exceptions import NotInplaceTranslatableError, UntranslatableTypeError
from rics.translation.exceptions import ConfigurationError


@pytest.mark.skip
def test_translate_without_id(hex_fetcher):
    # TODO: Formats without ID (#30)
    Translator(hex_fetcher, fmt="{hex}[, positive={positive}]").translate(1, names="positive_numbers")


def test_can_pickle(translator):
    from rics.utility.misc import serializable

    assert serializable(translator)


def test_offline(hex_fetcher):
    translator = Translator(hex_fetcher, fmt="{id}:{hex}[, positive={positive}]")
    translator.store()
    _translate(translator)


def test_online(translator):
    _translate(translator)


def test_mapping_error(translator):
    with pytest.raises(MappingError):
        translator.map_to_sources(0, names="unknown")


def _translate(translator):
    ans = translator.translate({"positive_numbers": list(range(-3, 3))})
    assert ans == {
        "positive_numbers": [
            "-3:-0x3, positive=False",
            "-2:-0x2, positive=False",
            "-1:-0x1, positive=False",
            "0:0x0, positive=True",
            "1:0x1, positive=True",
            "2:0x2, positive=True",
        ]
    }


@pytest.mark.parametrize(
    "data,clazz,kwargs",
    [
        (object(), UntranslatableTypeError, {"names": 1}),
        ((1, 2), AttributeError, {}),
        ((1, 2), NotInplaceTranslatableError, {"inplace": True, "names": "positive_numbers"}),
    ],
)
def test_bad_translatable(translator, data, clazz, kwargs):
    with pytest.raises(clazz):
        translator.translate(data, **kwargs)


def test_from_config():
    Translator.from_config("tests/translation/config.yaml")


def test_unknown_keys():
    with pytest.raises(ConfigurationError) as e:
        Translator.from_config("tests/translation/bad-config.yaml")

    assert "extra-key-that-should-not-exist" in str(e)


@pytest.mark.parametrize(
    "keep_predicate, reject_predicate, expected",
    [
        (lambda s: s.endswith("id"), None, ["ends_with_id", "also_ends_with_id"]),
        (lambda s: "numeric" not in s, None, ["ends_with_id", "also_ends_with_id", "difficult"]),
        (lambda s: "numeric" not in s, "difficult", ["ends_with_id", "also_ends_with_id"]),
    ],
    ids=["ENDS_WITH_ID", "NOT_NUMERIC", "NOT_NUMERIC_AND_WITHOUT_DIFFICULT"],
)
def test_name_predicates(translator, keep_predicate, reject_predicate, expected):
    data = {
        "ends_with_id": [1, 2, 3],
        "is_numeric": [3.5, 0.8, 1.1],
        "also_ends_with_id": [1, 2, 3],
        "also_numeric": [3.5, 0.8, 1.1],
        "difficult": [3.5, 0.8, 1.1],
    }

    names_to_translate = translator._resolve_names(data, keep_predicate, reject_predicate)

    assert names_to_translate == expected


@pytest.mark.filterwarnings("ignore: None of names")
def test_mapping_nothing_to_translate(translator):
    translator.map_to_sources({"strange-name": [1, 2, 3]})


@pytest.mark.filterwarnings("ignore: No names left to translate")
@pytest.mark.filterwarnings("ignore: None of names")
def test_all_name_ignored(translator):
    translator.map_to_sources({"name": []}, ignore_names="name")


@pytest.mark.filterwarnings("ignore: No names left to translate")
@pytest.mark.filterwarnings("ignore: None of names")
def test_explicit_name_ignored(translator):
    with pytest.raises(MappingError):
        translator.map_to_sources(0, names=["explicit_name"], ignore_names="explicit_name")
