import pandas as pd
import pytest

from rics.translation import Translator

from .conftest import DATE_COLUMNS, DVD_RENTAL_SKIP_REASON, wait_for_dvdrental


@pytest.fixture(scope="module")
def translator():
    extra_fetchers = ["tests/translation/dvdrental/sql-fetcher.toml"]
    config = "tests/translation/dvdrental/translation.toml"
    return Translator.from_config(config, extra_fetchers)


@pytest.mark.skipif(not wait_for_dvdrental(), reason=DVD_RENTAL_SKIP_REASON)
def test_dvd_rental(translator):
    expected = pd.read_csv("tests/translation/dvdrental/translated.csv", index_col=0, parse_dates=DATE_COLUMNS)

    with open("tests/translation/dvdrental/query.sql") as f:
        query = f.read()

    engine = translator._fetcher.fetchers[-1]._engine  # The SQL fetcher was given last
    df: pd.DataFrame = pd.read_sql(query, con=engine)
    translator.translate(df, inplace=True)

    assert (df.select_dtypes("datetime").columns == DATE_COLUMNS).all()
    actual = df.sample(len(expected), random_state=0)
    assert expected.equals(actual), actual.to_string()
