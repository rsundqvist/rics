import logging
import warnings
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Dict, Iterable, List, Optional, Set
from urllib.parse import quote_plus

import sqlalchemy

from rics.performance import format_perf_counter
from rics.translation.fetching import AbstractFetcher, exceptions, support
from rics.translation.fetching.types import FetchInstruction
from rics.translation.offline.types import PlaceholderTranslations
from rics.translation.types import IdType
from rics.utility.misc import read_env_or_literal, tname

LOGGER = logging.getLogger(__package__).getChild("SqlFetcher")


class SqlFetcher(AbstractFetcher[str, IdType]):
    """Fetch data from a SQL source. Requires SQLAlchemy.

    Args:
        connection_string: A SQLAlchemy connection string. Read from environment variable if `connection_string` starts
            with '@' followed by the name. Example: ``@TRANSLATION_DB_CONNECTION_STRING`` reads from
            the `TRANSLATION_DB_CONNECTION_STRING` environment variable.
        password: Password to insert into the connection string. Will be escaped to allow for special characters. If
            given, the connection string must contain a password key, eg; ``dialect://user:{password}@host:port``. Can
            be an environment variable just like `connection_string`.
        whitelist_tables: The only tables the ``SqlFetcher`` may access.
        blacklist_tables: The only tables the ``SqlFetcher`` may not access.
        include_views: If ``True``, discover views as well.
        fetch_in_below: Always use ``IN``-clause when fetching less than `fetch_in_below` IDs.
        fetch_between_over: Always use ``BETWEEN``-clause when fetching more than `fetch_between_over` IDs.
        fetch_between_max_overfetch_factor: If number of IDs to fetch is between `fetch_in_below` and
            `fetch_between_over`, use this factor to choose between ``IN`` and ``BETWEEN`` clause.
        fetch_all_limit: Maximum size of table to allow a fetch all-operation. 0=never allow. Ignore if ``None``.

    Raises:
        ValueError: If both `whitelist_tables` and `blacklist_tables` are given.
    """

    def __init__(
        self,
        connection_string: str,
        password: str = None,
        whitelist_tables: Iterable[str] = None,
        blacklist_tables: Iterable[str] = None,
        include_views: bool = True,
        fetch_in_below: int = 1200,
        fetch_between_over: int = 10_000,
        fetch_between_max_overfetch_factor: float = 2.5,
        fetch_all_limit: Optional[int] = 100_000,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        if whitelist_tables and blacklist_tables:
            raise ValueError("At most one of whitelist and blacklist may be given.")  # pragma: no cover

        self._engine = sqlalchemy.create_engine(self.parse_connection_string(connection_string, password))

        self._whitelist = set(whitelist_tables or [])
        self._blacklist = set(blacklist_tables or [])
        self._table_ts_dict: Optional[Dict[str, SqlFetcher.TableSummary]] = None
        self._reflect_views = include_views

        self._in_limit = fetch_in_below
        self._between_limit = fetch_between_over
        self._between_overfetch_limit = fetch_between_max_overfetch_factor
        self._fetch_all_limit = fetch_all_limit

    @property
    def _summaries(self) -> Dict[str, "SqlFetcher.TableSummary"]:
        """Names and sizes of tables that the ``SqlFetcher`` may interact with."""
        if self._table_ts_dict is None:
            start = perf_counter()
            ts_dict = self._get_summaries()
            if LOGGER.isEnabledFor(logging.INFO):
                sz = {name: ts.size for name, ts in sorted(ts_dict.items())}
                LOGGER.info(f"Processed {len(ts_dict)} tables in {format_perf_counter(start)}. Lengths={sz}.")
            self._table_ts_dict = ts_dict

        return self._table_ts_dict

    def fetch_translations(self, instr: FetchInstruction) -> PlaceholderTranslations:
        """Fetch columns from a SQL database."""
        ts = self._summaries[instr.source]
        columns = ts.select_columns(instr)
        select = sqlalchemy.select(map(ts.columns.get, columns))

        if instr.ids is None and not ts.fetch_all_permitted:  # pragma: no cover
            raise exceptions.ForbiddenOperationError(self._FETCH_ALL, f"disabled for table '{ts.name}'.")

        stmt = select if instr.ids is None else self._make_query(ts, select, set(instr.ids))
        return PlaceholderTranslations(instr.source, tuple(columns), tuple(self._engine.execute(stmt)))

    def _make_query(
        self, ts: "SqlFetcher.TableSummary", select: sqlalchemy.sql.Select, ids: Set[IdType]
    ) -> sqlalchemy.sql.Select:
        num_ids = len(ids)

        # Just fetch everything if we're getting "most of" the data anyway
        if ts.size < 25 or num_ids / ts.size > 0.9:
            if num_ids > ts.size:  # pragma: no cover
                warnings.warn(f"Fetching {num_ids} unique IDs from table '{ts.name}' which only has {ts.size} rows.")
            return select

        in_clause = select.where(ts.id_column.in_(ids))
        if num_ids < self._in_limit:
            return in_clause

        min_id = min(ids)
        max_id = max(ids)
        between_clause = select.where(ts.id_column.between(min_id, max_id))
        if isinstance(next(iter(ids)), str) or num_ids > self._between_limit:
            return between_clause

        try:
            overfetch_factor = (max_id - min_id) / num_ids  # type: ignore
        except TypeError:  # pragma: no cover
            return between_clause  # Non-numeric ID type

        if LOGGER.isEnabledFor(logging.DEBUG):
            s = "IN" if overfetch_factor > self._between_overfetch_limit else "BETWEEN"
            LOGGER.debug(f"Overfetch factor is {overfetch_factor:.2%}: Use {s}-clause.")

        return in_clause if overfetch_factor > self._between_overfetch_limit else between_clause

    @property
    def online(self) -> bool:
        return self._engine is not None  # pragma: no cover

    @property
    def sources(self) -> List[str]:
        return list(self._summaries)

    @property
    def placeholders(self) -> Dict[str, List[str]]:
        return {name: list(ts.columns.keys()) for name, ts in self._summaries.items()}

    @property
    def allow_fetch_all(self) -> bool:
        """:noindex:"""  # noqa: D400
        return super().allow_fetch_all and all(s.fetch_all_permitted for s in self._summaries.values())

    def __repr__(self) -> str:
        engine = self._engine
        tables = self.sources
        return f"{tname(self)}({engine=}, {tables=})"

    def close(self) -> None:  # pragma: no cover
        LOGGER.info("Deleting %s", self._engine)
        del self._engine
        self._engine = None

    @classmethod
    def parse_connection_string(cls, connection_string: str, password: Optional[str]) -> str:  # pragma: no cover
        """Parse a connection string. Read from environment if `connection_string` starts with '@'."""
        connection_string = read_env_or_literal(connection_string)
        if password:
            connection_string = connection_string.format(password=quote_plus(read_env_or_literal(password)))
        return connection_string

    def _get_summaries(self) -> Dict[str, "SqlFetcher.TableSummary"]:
        start = perf_counter()
        metadata = self.get_metadata()
        if LOGGER.isEnabledFor(logging.DEBUG):
            LOGGER.debug(f"Metadata created in {format_perf_counter(start)}.")

        table_names = set(metadata.tables)
        if self._whitelist:
            tables = self._whitelist  # pragma: no cover
        else:
            tables = table_names.difference(self._blacklist) if self._blacklist else table_names

        if not tables:  # pragma: no cover
            if self._whitelist:
                extra = " (whitelist)"
            elif self._blacklist:
                extra = f" (blacklist: {self._blacklist})"
            else:
                extra = ""

            raise ValueError(f"No sources found{extra}. Available tables: {table_names}")

        ans = {}
        for name in tables:
            table = metadata.tables[name]
            id_column = self.id_column(table.name, (c.name for c in table.columns))
            if id_column is None:  # pragma: no cover
                continue  # Mapper would've raised an error if we required all non-filtered tables to be mapped

            ans[name] = self.make_table_summary(table, table.columns[id_column])

        return ans

    def make_table_summary(
        self, table: sqlalchemy.sql.schema.Table, id_column: sqlalchemy.sql.schema.Column
    ) -> "SqlFetcher.TableSummary":
        """Create a table summary."""
        start = perf_counter()
        size = self.get_approximate_table_size(table, id_column)
        if LOGGER.isEnabledFor(logging.DEBUG):
            LOGGER.debug(f"Size of {table.name}={size} resolved in {format_perf_counter(start)}.")
        fetch_all_permitted = self._fetch_all_limit is None or size < self._fetch_all_limit
        return SqlFetcher.TableSummary(table.name, size, table.columns, fetch_all_permitted, id_column)

    def get_approximate_table_size(
        self,
        table: sqlalchemy.sql.schema.Table,
        id_column: sqlalchemy.sql.schema.Column,
    ) -> int:
        """Return the approximate size of a table.

        Called only by the :meth:`make_table_summary` method during discovery. The default implementation performs a
        count on the ID column, which may be expensive.

        Args:
            table: A table object.
            id_column: The ID column in `table`.

        Returns:
            An approximate size for `table`.
        """
        return self._engine.execute(sqlalchemy.func.count(id_column)).scalar()

    def get_metadata(self) -> sqlalchemy.MetaData:
        """Create a populated metadata object."""
        metadata = sqlalchemy.MetaData(self._engine)
        metadata.reflect(only=self._whitelist or None, views=self._reflect_views)
        return metadata

    @dataclass(frozen=True)
    class TableSummary:
        """Brief description of a known table."""

        name: str
        """Name of the table."""
        size: int
        """Approximate size of the table."""
        columns: sqlalchemy.sql.base.ColumnCollection
        """A flag indicating that the FETCH_ALL-operation is permitted for this table."""
        fetch_all_permitted: bool
        """A flag indicating that the FETCH_ALL-operation is permitted for this table."""
        id_column: sqlalchemy.schema.Column
        """The ID column of the table."""

        def select_columns(self, instr: FetchInstruction) -> List[str]:
            """Return required and optional columns of the table."""
            return support.select_placeholders(instr, self.columns.keys())
