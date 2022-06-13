import pandas as pd
import pytest


@pytest.mark.parametrize("ttype", [pd.DataFrame.from_dict, dict])
def test_translate_and_insert(imdb_translator, ttype):
    actual = imdb_translator.translate(ttype(UNTRANSLATED))

    if isinstance(actual, pd.DataFrame):
        actual = actual.to_dict(orient="list")

    assert actual == TRANSLATED


UNTRANSLATED = {
    "firstTitle": [3, 41064, 15, 41068, 41069],
    "nconst": [1, 15, 500, 30, 50],
}

TRANSLATED = {
    "firstTitle": [
        "3 not translated; default name=Title unknown",
        "41064:Think Fast (original: Think Fast) *1949†1950",
        "15 not translated; default name=Title unknown",
        "41068:Versatile Varieties (original: Versatile Varieties) *1949†1951",
        "41069:The Voice of Firestone (original: The Voice of Firestone) *1949†1963",
    ],
    "nconst": [
        "1:Fred Astaire *1899†1987",
        "15:James Dean *1931†1955",
        "500 not translated; default name=Name unknown",
        "30:Audrey Hepburn *1929†1993",
        "50:Groucho Marx *1890†1977",
    ],
}
