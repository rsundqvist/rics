import pytest

from rics.translation.factory import default_fetcher_factory
from rics.translation.fetching import MemoryFetcher


class AnotherFetcherType(MemoryFetcher):
    pass


@pytest.mark.parametrize(
    "clazz, expected_type",
    [
        ("MemoryFetcher", MemoryFetcher),
        ("rics.translation.fetching.MemoryFetcher", MemoryFetcher),
        ("tests.translation.test_factory.AnotherFetcherType", AnotherFetcherType),
    ],
)
def test_default_fetcher_factory(clazz, expected_type):
    fetcher = default_fetcher_factory(clazz, dict(data={}))
    assert isinstance(fetcher, expected_type)
