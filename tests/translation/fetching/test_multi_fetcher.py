import pandas as pd
import pytest

from rics.translation import Translator
from rics.translation.fetching import MemoryFetcher, MultiFetcher, SqlFetcher, exceptions
from rics.translation.fetching.types import IdsToFetch
from rics.translation.offline.types import PlaceholderTranslations


@pytest.fixture(scope="module")
def fetchers(data):
    humans_fetcher = MemoryFetcher({"humans": data["humans"]})
    empty_fetcher = MemoryFetcher({})
    everything_fetcher = MemoryFetcher(data)
    sql_fetcher = SqlFetcher("sqlite://", whitelist_tables=())  # No tables allowed!
    return humans_fetcher, empty_fetcher, everything_fetcher, sql_fetcher


@pytest.fixture(scope="module")
def multi_fetcher(fetchers):
    return MultiFetcher(*fetchers)


@pytest.fixture(scope="module")
def expected(data):
    return MemoryFetcher(data).fetch_all()


def test_sources(multi_fetcher):
    assert sorted(multi_fetcher.sources) == ["animals", "big_table", "huge_table", "humans"]


def test_sources_per_child(multi_fetcher):
    children = multi_fetcher.fetchers
    assert len(children) == 2
    assert children[0].sources == ["humans"]
    assert sorted(children[1].sources) == ["animals", "big_table", "huge_table", "humans"]


def test_placeholders(multi_fetcher):
    assert multi_fetcher.placeholders == {
        "animals": ["id", "name", "is_nice"],
        "humans": ["id", "name", "gender"],
        "big_table": ["id"],
        "huge_table": ["id"],
    }


def test_process_future():
    fetcher = MultiFetcher(*(MemoryFetcher({f"{i=}": {"id": []}}) for i in range(10)))

    ans = {}
    source_ranks = {}

    def make_and_process(rank):
        pht = PlaceholderTranslations.make("source", pd.DataFrame([rank], columns=["rank"]))
        fetcher._process_future_result({"source": pht}, rank=rank, source_ranks=source_ranks, ans=ans)
        return pht

    translations4 = make_and_process(4)
    assert ans["source"] == translations4

    with pytest.warns(exceptions.DuplicateSourceWarning):
        make_and_process(5)
    assert ans["source"] == translations4

    with pytest.warns(exceptions.DuplicateSourceWarning):
        translations2 = make_and_process(2)
    assert ans["source"] == translations2

    with pytest.warns(exceptions.DuplicateSourceWarning):
        translations0 = make_and_process(0)
    assert ans["source"] == translations0


def test_fetch_all(multi_fetcher, expected):
    with pytest.warns(exceptions.DuplicateSourceWarning):
        actual = multi_fetcher.fetch_all()
    assert actual == expected


def test_fetch(multi_fetcher, data):
    required = {"id"}
    placeholders = {"name", "is_nice"}

    sampled = [IdsToFetch(source, list(df.id)) for source, df in data.items()]
    expected = MemoryFetcher(data).fetch(sampled, placeholders, required=required)
    actual = multi_fetcher.fetch(sampled, placeholders, required=required)

    assert actual == expected


def test_ranks(multi_fetcher, fetchers):
    humans_fetcher, empty_fetcher, everything_fetcher, sql_fetcher = fetchers

    assert len(multi_fetcher.fetchers) == 2
    assert humans_fetcher in multi_fetcher.fetchers
    assert everything_fetcher in multi_fetcher.fetchers

    assert multi_fetcher._id_to_rank[id(humans_fetcher)] == 0
    assert multi_fetcher._id_to_rank[id(everything_fetcher)] == 2


def test_from_config():
    main_config = "tests/translation/config.imdb.toml"
    extra_fetchers = [
        "tests/translation/config.toml",
        "tests/translation/config.imdb.toml",
    ]
    Translator.from_config(main_config, extra_fetchers)
