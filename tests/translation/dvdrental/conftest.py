import os
from pathlib import Path

import pandas as pd
import sqlalchemy
import yaml  # type: ignore

from rics.translation import Translator

DIR = Path(__file__).parent.joinpath("docker")
CREDENTIALS = yaml.safe_load(DIR.joinpath("credentials.yml").read_text())["dialects"]
for k, v in dict(
    mysql="pymysql",
    postgresql="pg8000",
    mssql="pymssql",
).items():
    CREDENTIALS[k]["driver"] = v

QUERY = DIR.joinpath("tests/query.sql").read_text()


def check_status(dialect: str) -> None:
    engine = sqlalchemy.create_engine(get_connection_string(dialect))

    try:
        pd.read_sql("SELECT * FROM store", engine)
    except Exception:  # noqa: B902
        msg = (
            f"Unable to connect to database for {dialect=}. Start the databases"
            " by running:\n    ./run-docker-dvdrental.sh"
        )
        raise RuntimeError(msg)


def get_connection_string(dialect: str, with_password: bool = True) -> str:
    kwargs = CREDENTIALS[dialect]
    ans = "{dialect}+{driver}://{user}:{{password}}@localhost:{port}/sakila".format(dialect=dialect, **kwargs)
    return ans.format(password=kwargs["password"]) if with_password else ans


def get_translator(dialect: str) -> Translator[str, str, int]:
    os.environ["DVDRENTAL_PASSWORD"] = "Sofia123!"
    os.environ["DVDRENTAL_CONNECTION_STRING"] = get_connection_string(dialect, with_password=False)
    extra_fetchers = ["tests/translation/dvdrental/sql-fetcher.toml"]
    config = "tests/translation/dvdrental/translation.toml"
    return Translator.from_config(config, extra_fetchers)
