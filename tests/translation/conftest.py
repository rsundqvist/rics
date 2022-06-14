from typing import Any, Iterable, List, Optional, Tuple

import pytest

from rics.translation import Translator
from rics.translation.fetching import Fetcher
from rics.translation.fetching._fetch_instruction import FetchInstruction
from rics.translation.fetching.exceptions import UnknownIdError
from rics.translation.offline.types import PlaceholderTranslations


class HexFetcher(Fetcher[str, int, str]):
    def __init__(self) -> None:
        self.num_fetches = 0
        super().__init__()

    def fetch_placeholders(self, instr: FetchInstruction) -> PlaceholderTranslations:
        self.num_fetches += 1

        placeholders = Fetcher.select_placeholders(instr, ["id", "hex", "positive"])

        return Fetcher.make_and_verify(
            instr,
            placeholders,
            tuple(self._run(placeholders, instr.ids)),
        )

    @staticmethod
    def _run(placeholders: List[str], ids: Optional[Iterable[int]]) -> Iterable[Tuple[Any, ...]]:
        ids = tuple(range(-10, 10) if ids is None else ids)
        if max(ids) > 9 or min(ids) < -10:
            raise UnknownIdError()

        funcs = {
            "hex": hex,
            "id": lambda x: x,
            "positive": lambda x: x >= 0,
        }

        for idx in ids:
            yield tuple(funcs[p](idx) for p in placeholders)

    @property
    def sources(self) -> List[str]:
        return ["positive_numbers", "negative_numbers"]


@pytest.fixture(scope="session")
def hex_fetcher():
    yield HexFetcher()


@pytest.fixture(scope="session")
def translator(hex_fetcher):
    yield Translator(hex_fetcher, fmt="{id}:{hex}[, positive={positive}]")


@pytest.fixture(scope="session")
def imdb_translator():
    yield Translator.from_config("tests/translation/config.imdb.yaml")


@pytest.fixture(scope="module")
def translation_map(imdb_translator):
    imdb_translator.store({"firstTitle": [], "nconst": []})
    yield imdb_translator._cached_tmap
