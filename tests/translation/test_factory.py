from typing import Any, Optional, Type

import pytest

from rics.translation import Translator
from rics.translation.factory import TranslatorFactory, default_fetcher_factory
from rics.translation.fetching import AbstractFetcher, MemoryFetcher
from rics.translation.types import IdType, SourceType


class AnotherFetcherType(MemoryFetcher[SourceType, IdType]):
    pass


@pytest.mark.parametrize(
    "clazz, expected_type",
    [
        ("MemoryFetcher", MemoryFetcher),
        ("rics.translation.fetching.MemoryFetcher", MemoryFetcher),
        ("tests.translation.test_factory.AnotherFetcherType", AnotherFetcherType),
    ],
)
def test_default_fetcher_factory(
    clazz: str,
    expected_type: Type[AbstractFetcher[Any, Any]],
) -> None:
    fetcher: AbstractFetcher[str, int] = default_fetcher_factory(clazz, dict(data={}))
    assert isinstance(fetcher, expected_type)


@pytest.mark.parametrize("arg", [None, "rics.translation.Translator", "rics.translation._translator.Translator"])
def test_resolve_class(arg: Optional[Type[Translator[Any, Any, Any]]]) -> None:
    assert TranslatorFactory.resolve_class(arg) == Translator
