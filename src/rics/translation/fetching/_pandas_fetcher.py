import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Union

import pandas as pd

from rics.translation.fetching._fetch_instruction import FetchInstruction
from rics.translation.fetching._fetcher import Fetcher
from rics.translation.offline.types import IdType, NameType
from rics.utility.misc import PathLikeType, tname

LOGGER = logging.getLogger(__package__).getChild("PandasFetcher")
PandasReadFunction = Callable[[PathLikeType, Any, Any], pd.DataFrame]


class PandasFetcher(Fetcher[NameType, IdType, str]):
    """Fetcher using pandas DataFrames as the data format.

    Fetch data from serialized DataFrames. How this is done is determined by `read_function`. This is typically a Pandas
    function such as :func:`pandas.read_csv` or :func:`pandas.read_pickle`, but any function that accepts a string
    `source` as the  first argument and returns a data frame can be used.

    The read function is invoked for sources found in `sources` but not in `source_frames`.

    Args:
        read_function: A Pandas `read`-function.
        read_path_format: A formatting string or a callable to apply to a source before passing them to `read_function`.
            Must contain a `source` as its only placeholder. Example: ``data/{source}.pkl``. None=leave as-is.
        read_function_args: Additional positional arguments for `read_function`.
        read_function_kwargs: Additional keyword arguments for `read_function`.

    See Also:
        Official `Pandas IO documentation`_.

    .. _Pandas IO documentation:
        https://pandas.pydata.org/pandas-docs/stable/user_guide/io.html
    """

    def __init__(
        self,
        read_function: PandasReadFunction = pd.read_pickle,
        read_path_format: Optional[Union[str, Callable[[str], str]]] = "data/{}.pkl",
        read_function_args: Iterable[Any] = None,
        read_function_kwargs: Mapping[str, Any] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._read = read_function
        self._format_source: Callable[[str], str] = _make_format_fn(read_path_format)
        self._args = read_function_args or ()
        self._kwargs = read_function_kwargs or {}

        self._source_paths: Dict[str, Path] = {}
        self._sources: List[str] = []

    def read(self, source_path: PathLikeType) -> pd.DataFrame:
        """Read a DataFrame from a source path.

        Args:
            source_path: Path to serialized DataFrame.

        Returns:
            A deserialized DataFrame.
        """
        return self._read(source_path, *self._args, **self._kwargs)

    def find_sources(self) -> Dict[str, Path]:
        """Search for source paths to pass to `read_function` using `read_path_format`.

        Returns:
            A dict ``{source, path}``.

        Raises:
            IOError: If files cannot be read.
        """
        abs_file = Path(self._format_source("")).absolute()
        directory = abs_file.parent
        file_pattern = abs_file.name

        if not directory.is_dir():
            problem = "is not a directory" if directory.exists() else "does not exist"
            raise IOError(f"Bad path format: {directory} {problem}.")

        source_paths = {}
        # Path.glob does not work with absolute directories.
        for file in map(Path, os.listdir(directory)):
            if file.name.endswith(str(file_pattern)):
                source_paths[file.name.replace(file_pattern, "")] = directory.joinpath(file)

        if not source_paths:
            pattern = Path(self._format_source("*")).absolute()
            raise IOError(f"Bad path pattern: '{pattern}' did not match any files.")

        return source_paths

    @property
    def sources(self) -> List[str]:
        """Source names known to the fetcher, such as ``cities`` or ``languages``."""
        if not self._sources:
            if not self._source_paths:
                self._source_paths = self.find_sources()
            self._sources = list(self._source_paths)
            LOGGER.debug("Sources initialized: %s", self._sources)

        return self._sources

    def fetch_placeholders(self, instr: FetchInstruction) -> pd.DataFrame:
        """Read columns from a serialized dataframe."""
        source_path = self._source_paths[instr.source]
        return self.read(source_path)

    def __repr__(self) -> str:
        return f"{tname(self)}(read_function={tname(self._read)})"


def _make_format_fn(read_path_format: Optional[Union[str, Callable[[str], str]]]) -> Callable[[str], str]:
    if callable(read_path_format):
        return read_path_format

    # At this point read_path_format is a string or None
    return (read_path_format or "{}").format
