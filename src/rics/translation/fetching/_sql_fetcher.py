import logging
from typing import Any, Iterable, List, Optional
from urllib.parse import quote_plus

import pandas as pd

from rics.translation.fetching import Fetcher
from rics.translation.fetching._fetch_instruction import FetchInstruction
from rics.translation.offline.types import IdType, PlaceholdersDict
from rics.utility.misc import read_env_or_literal, tname

LOGGER = logging.getLogger(__package__).getChild("SqlFetcher")

try:
    import sqlalchemy

    _SQLALCHEMY_INSTALLED = True
except ModuleNotFoundError:
    _SQLALCHEMY_INSTALLED = False


class SqlFetcher(Fetcher[str, IdType, str]):
    """Fetch data from a SQL source. Requires SQLAlchemy.

    Args:
        connection_string: A SQLAlchemy connection string. Read from environment variable if `connection_string` starts
            with '@' followed by the name. Example: ``@TRANSLATION_DB_CONNECTION_STRING`` reads from
            the `TRANSLATION_DB_CONNECTION_STRING` environment variable.
        password: Password to insert into the connection string. Will be escaped to allow for special characters. If
            given, the connection string must contain a password key, eg; ``dialect://user:{password}@host:port``. Can
            be an environment variable just like `connection_string`.
        whitelist_tables: The only tables the fetcher may access.
        blacklist_tables: The only tables the fetcher may not access.

    Raises:
        ValueError: If both `blacklist` and `whitelist` are given.
        ModuleNotFoundError: If SQLAlchemy is not installed.
    """

    def __init__(
        self,
        connection_string: str,
        password: str = None,
        whitelist_tables: Iterable[str] = None,
        blacklist_tables: Iterable[str] = None,
        **kwargs: Any,
    ) -> None:
        if not _SQLALCHEMY_INSTALLED:
            raise ModuleNotFoundError("Install SQLAlchemy and the extras for your SQL flavor to use SQL fetching.")

        super().__init__(**kwargs)

        if whitelist_tables and blacklist_tables:
            raise ValueError("At most one of whitelist and blacklist may be given.")

        self._engine = sqlalchemy.create_engine(self.parse_connection_string(connection_string, password))
        self._sanitizer = sqlalchemy.String().literal_processor(dialect=self._engine.dialect)

        if whitelist_tables:
            self._sources = list(whitelist_tables)
        elif blacklist_tables:
            self._sources = []  # TODO
            raise NotImplementedError("blacklist_tables not implemented yet")

    def sanitize_id(self, arg: IdType) -> IdType:
        """Sanitize an input."""
        # Doesn't work with SQLAlchemy table names
        if isinstance(arg, int):
            return arg
        elif isinstance(arg, str):
            return self._sanitizer(arg)

        raise TypeError(f"Cannot sanitize {arg}")

    @staticmethod
    def sanitize_table(table: str) -> str:
        """Sanitize a table name."""
        if not table.replace("_", "").isalnum():
            raise ValueError(f"Invalid table: {table}")
        return table

    def fetch_placeholders(self, instr: FetchInstruction) -> PlaceholdersDict:
        """Fetch columns from a SQL database."""
        self.assert_online()
        table = self.sanitize_table(instr.source)
        return pd.read_sql_table(table, self._engine, columns=instr.required)

    @property
    def online(self) -> bool:
        """Return connectivity status. If False, no new translations may be fetched."""
        return self._engine is not None

    @property
    def sources(self) -> List[str]:
        """Source names known to the fetcher, such as ``cities`` or ``languages``."""
        return self._sources

    def __repr__(self) -> str:
        engine = self._engine
        tables = self.sources
        return f"{tname(self)}({engine=}, {tables=})"

    def close(self) -> None:
        """Close database connection."""
        LOGGER.debug(f"Deleting {self._engine}")
        del self._engine
        self._engine = None

    @classmethod
    def parse_connection_string(cls, connection_string: str, password: Optional[str]) -> str:
        """Parse a connection string. Read from environment if `connection_string` starts with '@'."""
        connection_string = read_env_or_literal(connection_string)
        if password:
            connection_string = connection_string.format(password=quote_plus(read_env_or_literal(password)))
        return connection_string
