import pandas as pd
import pytest as pytest

from rics.translation.fetching import SqlFetcher


def test_table_sizes(sql_fetcher):
    actual_sizes = {ts.name: ts.size for ts in sql_fetcher._get_summaries().values()}

    assert actual_sizes == {
        "animals": 3,
        "humans": 2,
        "big_table": 100,
        "huge_table": 1000,
    }


@pytest.mark.parametrize("table_to_verify", ["animals", "humans", "big_table", "huge_table"])
def test_fetch_all(sql_fetcher, data, table_to_verify):
    actual = sql_fetcher.fetch_all(["id"], ["name", "is_nice", "gender"])[table_to_verify]
    expected = data[table_to_verify].to_dict(orient="list")
    assert actual == expected


@pytest.fixture(scope="module")
def sql_fetcher(connection_string):
    yield SqlFetcher(connection_string)


@pytest.fixture(scope="module")
def connection_string(data):
    import os

    import sqlalchemy

    db_file = "test-database.sqlite"

    if os.path.exists(db_file):
        os.remove(db_file)

    connection_string = f"sqlite:///{db_file}"
    engine = sqlalchemy.create_engine(connection_string)
    insert_data(engine, data)

    yield connection_string

    os.remove(db_file)


def insert_data(engine, data):
    for table, table_data in data.items():
        table_data.to_sql(table, engine, index=False)


@pytest.fixture(scope="module")
def data():
    return {
        "animals": pd.DataFrame(
            {"id": [0, 1, 2], "name": ["Tarzan", "Morris", "Simba"], "is_nice": [False, True, True]}
        ),
        "humans": pd.DataFrame({"id": [1991, 1999], "name": ["Richard", "Sofia"], "gender": ["Male", "Female"]}),
        "big_table": pd.DataFrame({"id": range(100)}),
        "huge_table": pd.DataFrame({"id": range(1000)}),
    }
