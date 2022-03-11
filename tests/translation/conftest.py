from typing import Any, Iterable, List, Optional, Tuple

import pytest

from rics.translation import Translator
from rics.translation.fetching import Fetcher
from rics.translation.fetching._fetch_instruction import FetchInstruction
from rics.translation.fetching.exceptions import UnknownIdError
from rics.translation.offline.types import PlaceholdersDict


class HexFetcher(Fetcher[str, int, str]):
    def __init__(self) -> None:
        super().__init__(True)

    def fetch_placeholders(self, instr: FetchInstruction) -> PlaceholdersDict:
        """Convert integers."""
        if instr.ids is not None:
            for idx in instr.ids:
                if not isinstance(idx, int):
                    # Mypy?
                    ValueError(f"IDs must be integers, got: {instr.ids}")

        placeholders = instr.required + instr.optional
        return {ph: self._convert(ph, instr.ids) for ph in placeholders}

    @property
    def sources(self) -> List[str]:
        return ["positive_numbers", "negative_numbers"]

    @staticmethod
    def _convert(key: str, ids: Optional[Iterable[int]]) -> Tuple[Any, ...]:
        ids = tuple(range(-10, 10) if ids is None else ids)

        if max(ids) > 9 or min(ids) < -10:
            raise UnknownIdError()

        if key == "id":
            return ids

        assert key in ["hex", "positive"]

        if key == "hex":
            return tuple(map(hex, ids))
        if key == "positive":
            return tuple(x >= 0 for x in ids)

        raise AssertionError("This wasn't supposed to happen.")


@pytest.fixture(scope="session")
def hex_fetcher():
    yield HexFetcher()


@pytest.fixture(scope="session")
def translator(hex_fetcher):
    yield Translator(hex_fetcher, fmt="{id}:{hex}[, positive={positive}]")
