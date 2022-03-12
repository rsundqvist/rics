import logging
import warnings
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, Iterable, List, Optional
from urllib.parse import quote_plus

from rics.translation.fetching import Fetcher, exceptions
from rics.translation.fetching._fetch_instruction import FetchInstruction
from rics.translation.offline.types import IdType, PlaceholdersDict
from rics.utility.misc import read_env_or_literal, tname

LOGGER = logging.getLogger(__package__).getChild("SqlFetcher")

try:
    import sqlalchemy

    _SQLALCHEMY_INSTALLED = True
except ModuleNotFoundError:
    _SQLALCHEMY_INSTALLED = False


@dataclass(frozen=True)
class TableSummary:
    """Brief description of a known table."""

    name: str
    size: int
    columns: sqlalchemy.sql.base.ImmutableColumnCollection
    fetch_all_permitted: bool
    # id_columns: str  # TODO hämta mha overrides

    def select_columns(self, required: Iterable[str], optional: Iterable[str]) -> List[str]:
        """Return required and optional columns of the table."""
        required_columns = set(required)
        known_column_names = set(self.columns.keys())
        missing = required_columns.difference(known_column_names)
        if missing:
            raise ValueError(f"Table '{self.name}' missing required columns {missing}.")

        optional_columns = known_column_names.intersection(optional)
        return list(required_columns.union(optional_columns))


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

        self._whitelist = set(whitelist_tables or [])
        self._blacklist = set(blacklist_tables or [])
        self._table_ts_dict: Optional[Dict[str, TableSummary]] = None
        self._in_limit = fetch_in_below
        self._between_limit = fetch_between_over
        self._between_overfetch_limit = fetch_between_max_overfetch_factor
        self._fetch_all_limit = fetch_all_limit

    @property
    def _summaries(self) -> Dict[str, TableSummary]:
        """Names and sizes of tables that the fetcher may interact with."""
        if self._table_ts_dict is None:
            ts_dict = self._get_summaries()
            LOGGER.info("Table discovery found %d tables: %s", len(ts_dict), sorted(ts_dict))
            self._table_ts_dict = ts_dict

        return self._table_ts_dict

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
        table = self.sanitize_table(instr.source)
        columns = self._summaries[table].select_columns(instr.required, instr.optional)
        return pd.read_sql_table(table, self._engine, columns=columns)

    @property
    def online(self) -> bool:
        """Return connectivity status. If False, no new translations may be fetched."""
        return self._engine is not None

    @property
    def sources(self) -> List[str]:
        """Source names known to the fetcher, such as ``cities`` or ``languages``."""
        return list(self._summaries)

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

    def _get_summaries(self) -> Dict[str, TableSummary]:
        metadata = sqlalchemy.MetaData(self._engine)
        metadata.reflect()
        table_names = set(metadata.tables)

        if self._whitelist:
            tables = self._whitelist.intersection(table_names)
        elif self._blacklist:
            tables = set(table_names).difference(self._blacklist)
        else:
            tables = table_names

        if not tables:  # pragma: no cover
            if self._whitelist:
                extra = f" whitelisted tables: {self._whitelist}"
            elif self._whitelist:
                extra = f" blacklisted tables: {self._whitelist}"
            else:
                extra = ""

            warnings.warn(f"No tables found with{extra}. Available tables: {table_names}")
            return {}

        ans = {}
        for name in tables:
            size = next(self._engine.execute(sqlalchemy.select(sqlalchemy.text(f"count(*) AS count FROM {name}"))))[0]
            columns = frozenset(column.key for column in metadata.tables[name].columns)
            ans[name] = TableSummary(name, size, columns)

        return ans
