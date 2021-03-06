from itertools import combinations_with_replacement

import numpy as np
import pandas as pd
import pytest

from rics.mapping import Mapper
from rics.mapping.exceptions import MappingError, MappingWarning
from rics.translation import Translator
from rics.translation.dio.exceptions import NotInplaceTranslatableError, UntranslatableTypeError
from rics.translation.exceptions import ConfigurationError, TooManyFailedTranslationsError
from rics.translation.fetching.exceptions import UnknownSourceError


@pytest.mark.parametrize("with_id, with_override, store", combinations_with_replacement([False, True], 3))
def test_dummy_translation_doesnt_crash(with_id, with_override, store):
    with pytest.warns(UserWarning):
        t = Translator(fmt="{id}:{first}:{second}:{third}")

    names = list(map("placeholder{}".format, range(3)))
    data = np.random.randint(0, 100, (3, 10))

    def override_function(name, *args):  # noqa
        return names[0] if name == "id" else None

    if with_id:
        names[0] = "id"
    if store:
        t.store(data, names=names)

    ans = t.translate(data, names=names, override_function=override_function if with_override else None)
    assert pd.DataFrame(ans.T, columns=names).shape == (10, 3)


def test_translate_without_id(hex_fetcher):
    without_id = "{hex}, positive={positive}"
    ans = Translator(hex_fetcher, fmt=without_id).translate({"positive_numbers": list(range(-1, 2))})
    assert ans == {
        "positive_numbers": [
            "-0x1, positive=False",
            "0x0, positive=True",
            "0x1, positive=True",
        ]
    }


@pytest.mark.parametrize("copy", [False, True])
def test_can_pickle(translator, copy):
    from rics.utility.misc import serializable

    assert serializable(translator.copy() if copy else translator)


@pytest.mark.parametrize("copy", [False, True])
def test_offline(hex_fetcher, copy):
    translator = Translator(hex_fetcher, fmt="{id}:{hex}[, positive={positive}]").store()
    if copy:
        translator = translator.copy()
    _translate(translator)


@pytest.mark.parametrize("copy", [False, True])
def test_online(translator, copy):
    _translate(translator.copy() if copy else translator)


def test_mapping_error(translator):
    with pytest.raises(MappingError):
        translator.map(0, names="unknown")


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
    Translator.from_config("tests/translation/config.toml")


def test_missing_config():
    with pytest.raises(ConfigurationError):
        Translator.from_config("tests/translation/bad-config.toml")


def test_store_and_restore(hex_fetcher):
    from tempfile import TemporaryDirectory

    translator = Translator(hex_fetcher, fmt="{id}:{hex}")

    data = {
        "positive_numbers": list(range(0, 5)),
        "negative_numbers": list(range(-5, -1)),
    }
    translated_data = translator(data)

    with TemporaryDirectory("test-store-and-restore", "rics") as tmpdir:
        path = f"{tmpdir}/test-translator.pkl"
        translator.store(path=path)
        restored = Translator.restore(path=path)

    translated_by_restored = restored(data)
    assert translated_by_restored == translated_data


def test_store_with_explicit_values(hex_fetcher):
    data = {
        "positive_numbers": list(range(0, 5)),
        "negative_numbers": list(range(-5, -1)),
    }
    translator = Translator(
        hex_fetcher, fmt="{hex}", default_fmt="{id} not known", mapper=Mapper(unmapped_values_action="ignore")
    )

    with pytest.raises(MappingError) as e, pytest.warns(UserWarning) as w:
        translator.store(data, ignore_names=data, delete_fetcher=False)
        assert "No names left" in str(w)
        assert "not store" in str(e)

    translator.store(data)
    expected_num_fetches = hex_fetcher.num_fetches
    assert sorted(translator._cached_tmap.sources) == sorted(data)
    actual = translator.translate(data)
    assert hex_fetcher.num_fetches == expected_num_fetches
    assert actual == {
        "positive_numbers": list(map(hex, range(0, 5))),
        "negative_numbers": list(map(hex, range(-5, -1))),
    }

    unknown_data = {
        "positive_numbers": [5, 6],
        "negative_numbers": [-100, -6],
    }
    assert translator.translate(unknown_data) == {
        "positive_numbers": ["5 not known", "6 not known"],
        "negative_numbers": ["-100 not known", "-6 not known"],
    }


@pytest.mark.parametrize(
    "reject_predicate, expected",
    [
        (lambda s: not s.endswith("id"), ["ends_with_id", "also_ends_with_id"]),
        (lambda s: "numeric" in s, ["ends_with_id", "also_ends_with_id"]),
        (None, ["ends_with_id", "is_numeric", "also_ends_with_id", "also_numeric"]),
    ],
)
def test_reject_predicates(translator, reject_predicate, expected):
    data = {
        "ends_with_id": [1, 2, 3],
        "is_numeric": [3.5, 0.8, 1.1],
        "also_ends_with_id": [1, 2, 3],
        "also_numeric": [3.5, 0.8, 1.1],
    }
    names_to_translate = translator._resolve_names(data, names=data, ignored_names=reject_predicate)

    assert names_to_translate == expected


def test_mapping_nothing_to_translate(translator):
    with pytest.warns(MappingWarning) as w:
        translator.map({"strange-name": [1, 2, 3]})
    assert len(w) == 1
    assert "none of names=None" in str(w[0])


def test_all_name_ignored(translator):
    with pytest.warns(MappingWarning) as w:
        translator.map({"name": []}, ignore_names="name")
    assert len(w) == 2
    assert "No names left" in str(w[0])
    assert "none of names=None" in str(w[1])


def test_explicit_name_ignored(translator):
    with pytest.warns(UserWarning) as w, pytest.raises(MappingError) as e:
        translator.map(0, names=["explicit_name"], ignore_names="explicit_name")
    assert "Required names" in str(e)
    assert len(w) == 1
    assert "No names left" in str(w[0])


def test_complex_default(hex_fetcher):
    fmt = "{id}:{hex}[, positive={positive}]"
    default_fmt = "{id} - {hex} - {positive}"
    default_fmt_placeholders = {"default": {"positive": "POSITIVE/NEGATIVE", "hex": "HEX"}}
    t = Translator(
        hex_fetcher, fmt=fmt, default_fmt=default_fmt, default_fmt_placeholders=default_fmt_placeholders
    ).store()

    in_range = t.translate({"positive_numbers": list(range(-1, 2))})
    assert in_range == {
        "positive_numbers": [
            "-1:-0x1, positive=False",
            "0:0x0, positive=True",
            "1:0x1, positive=True",
        ]
    }

    out_of_range = t.translate({"positive_numbers": [-5000, 10000]})
    assert out_of_range == {
        "positive_numbers": [
            "-5000 - HEX - POSITIVE/NEGATIVE",
            "10000 - HEX - POSITIVE/NEGATIVE",
        ]
    }


def test_id_only_default(hex_fetcher):
    fmt = "{id}:{hex}[, positive={positive}]"
    default_fmt = "{id} is not known"
    t = Translator(hex_fetcher, fmt=fmt, default_fmt=default_fmt).store()

    in_range = t.translate({"positive_numbers": list(range(-1, 2))})
    assert in_range == {
        "positive_numbers": [
            "-1:-0x1, positive=False",
            "0:0x0, positive=True",
            "1:0x1, positive=True",
        ]
    }

    out_of_range = t.translate({"positive_numbers": [-5000, 10000]})
    assert out_of_range == {
        "positive_numbers": [
            "-5000 is not known",
            "10000 is not known",
        ]
    }


def test_extra_placeholder():
    t = Translator(
        {"people": {"id": [1999], "name": ["Sofia"]}},
        default_fmt="{id}:{right}",
        default_fmt_placeholders=dict(default={"left": "left-value", "right": "right-value"}),
    )
    assert "1:right-value" == t(1, names="people")

    t = t.copy(default_fmt="{left}, {right}")
    assert "left-value, right-value" == t(1, names="people")

    t = t.copy(default_fmt_placeholders=dict(default={"left": "LEFT", "right": "RIGHT"}))
    assert "LEFT, RIGHT" == t(1, names="people")


def test_plain_default(hex_fetcher):
    fmt = "{id}:{hex}[, positive={positive}]"
    default_fmt = "UNKNOWN"
    t = Translator(hex_fetcher, fmt=fmt, default_fmt=default_fmt).store()

    in_range = t.translate({"positive_numbers": list(range(-1, 2))})
    assert in_range == {
        "positive_numbers": [
            "-1:-0x1, positive=False",
            "0:0x0, positive=True",
            "1:0x1, positive=True",
        ]
    }

    out_of_range = t.translate({"positive_numbers": [-5000, 10000]})
    assert out_of_range == {"positive_numbers": ["UNKNOWN", "UNKNOWN"]}


def test_no_default(hex_fetcher):
    fmt = "{id}:{hex}[, positive={positive}]"
    t = Translator(hex_fetcher, fmt=fmt).store()
    in_range = t.translate({"positive_numbers": list(range(-1, 2))})
    assert in_range == {
        "positive_numbers": [
            "-1:-0x1, positive=False",
            "0:0x0, positive=True",
            "1:0x1, positive=True",
        ]
    }

    out_of_range = t.translate({"positive_numbers": [-5000, 10000]})
    assert out_of_range == {
        "positive_numbers": [None, None],
    }


def test_imdb_discovery(imdb_translator):
    assert sorted(imdb_translator._fetcher.sources) == ["name_basics", "title_basics"]


def test_copy_with_override(imdb_translator):
    data = {"nconst": [1, 15]}

    assert imdb_translator.translate(data) == {
        "nconst": ["1:Fred Astaire from: 1899, to: 1987", "15:James Dean from: 1931, to: 1955"]
    }

    copy0 = imdb_translator.copy(fmt="Number {id} is {name}")
    assert copy0.translate(data) == {"nconst": ["Number 1 is Fred Astaire", "Number 15 is James Dean"]}

    copy1 = imdb_translator.copy(fmt="{name}")
    assert copy1.translate(data) == {"nconst": ["Fred Astaire", "James Dean"]}


def test_no_names(translator):
    with pytest.raises(AttributeError):
        translator.translate(pd.Series(range(3)))


def test_untranslated_fraction():
    translator = Translator({"source": {"id": [0], "name": ["zero"]}}, default_fmt="{id} not translated")

    translator.translate([0, 1], names="source", maximal_untranslated_fraction=0.5)

    with pytest.raises(TooManyFailedTranslationsError):
        translator.translate([0, 0, 1], names="source", maximal_untranslated_fraction=0.0)

    with pytest.raises(TooManyFailedTranslationsError):
        translator.translate(1, names="source", maximal_untranslated_fraction=0.0)


def test_reverse(hex_fetcher):
    fmt = "{id}:{hex}[, positive={positive}]"
    t = Translator(hex_fetcher, fmt=fmt).store()
    expected = {"positive_numbers": list(range(-1, 2))}
    translated = t.translate(expected.copy())

    assert translated == {
        "positive_numbers": [
            "-1:-0x1, positive=False",
            "0:0x0, positive=True",
            "1:0x1, positive=True",
        ]
    }

    actual = t.translate(translated, reverse=True)
    assert expected == actual


def test_simple_function_overrides(translator):
    actual = translator.translate(1, names="whatever", override_function=lambda *args: "positive_numbers")
    assert actual == "1:0x1, positive=True"

    actual = translator.translate(1, names="positive_numbers", override_function=lambda *args: None)
    assert actual == "1:0x1, positive=True"

    with pytest.raises(UnknownSourceError):
        translator.translate(1, names="whatever", override_function=lambda *args: "bad")


def test_complex_function_overrides(translator):
    with pytest.raises(NotImplementedError) as e:
        translator.translate(1, names="whatever", override_function=lambda *args: {})

    assert "https://github.com/rsundqvist/rics/issues/64" in str(e.value)


def test_override_fetcher(translator):
    old_fetcher = translator.fetcher
    assert "1:0x1, positive=True" == translator.translate(1, names="positive_numbers")
    expected = old_fetcher.num_fetches

    translator = translator.copy(fetcher={"positive_numbers": {"id": [1], "hex": ["0x1"], "positive": [True]}})
    assert "1:0x1, positive=True" == translator.translate(1, names="positive_numbers")
    assert expected == old_fetcher.num_fetches


def test_translate_attribute():
    with pytest.warns(UserWarning):
        translate = Translator().translate
    df = pd.DataFrame(range(3))
    df.index.name = "index-name"

    translate(df, attribute="index")

    assert df.index.tolist() == translate(list(range(3)), names=df.index.name)


def test_inherited_name(translator):
    assert translator._allow_name_inheritance
    s = pd.Series([1, 1, 2, 2, 2, 3, 4], name="positive_numbers")

    translator.translate(s, attribute="index")

    s.name = None
    with pytest.raises(AttributeError):
        translator.translate(s, attribute="index")
