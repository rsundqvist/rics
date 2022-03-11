import pytest

from rics.mapping.exceptions import MappingError
from rics.translation import Translator
from rics.translation.dio.exceptions import NotInplaceTranslatableError, UntranslatableTypeError
from rics.translation.exceptions import ConfigurationError


@pytest.mark.skip
def test_positional_args():
    args = ("This is no good!", "We don't want positional arguments!", True)
    with pytest.raises(AssertionError) as e:
        Translator(*args)

    for arg in args:
        assert str(arg) in str(e.value)


def test_can_pickle(translator):
    from rics.utility.misc import serializable

    assert serializable(translator)


def test_offline(hex_fetcher):
    translator = Translator(hex_fetcher, fmt="{id}:{hex}[, positive={positive}]")
    translator.store()
    _translate(translator)


def test_mapping_error(translator):
    with pytest.raises(MappingError):
        translator.translate(0, names="unknown")


def test_online(translator):
    _translate(translator)


@pytest.mark.filterwarnings("ignore: None of names")
def test_mapping_nothing_to_translate(translator):
    translator.translate({"strange-name": [1, 2, 3]})


@pytest.mark.filterwarnings("ignore: No names left to translate")
@pytest.mark.filterwarnings("ignore: None of names")
def test_all_names_ignored(translator):
    translator.translate(0, names="name", ignore_names="name")


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
