import pandas as pd
import pytest

from rics.translation import Translator

from .conftest import DATE_COLUMNS, DVD_RENTAL_SKIP_REASON, wait_for_dvdrental


@pytest.mark.skipif(not wait_for_dvdrental(), reason=DVD_RENTAL_SKIP_REASON)
def test_dvd_rental():
    translator = Translator.from_config("tests/translation/dvdrental/config.toml")
    expected = pd.read_csv("tests/translation/dvdrental/translated.csv", index_col=0, parse_dates=DATE_COLUMNS)

    with open("tests/translation/dvdrental/query.sql") as f:
        query = f.read()

    df: pd.DataFrame = pd.read_sql(query, con=translator._fetcher._engine)
    translator.translate(df, inplace=True)

    assert (df.select_dtypes("datetime").columns == DATE_COLUMNS).all()
    actual = df.sample(len(expected), random_state=0)
    assert expected.equals(actual), actual.to_string()
