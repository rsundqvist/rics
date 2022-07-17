"""Factory functions for translation classes."""
from typing import TYPE_CHECKING, Any, Callable, Dict
from typing import Generic as _Generic
from typing import Iterable, Optional, Tuple, Union

import toml

from rics._internal_support.types import PathLikeType
from rics.mapping import HeuristicScore as _HeuristicScore
from rics.mapping import Mapper as _Mapper
from rics.translation import exceptions, fetching
from rics.translation.types import IdType, NameType, SourceType
from rics.utility import misc
from rics.utility.action_level import ActionLevel as _ActionLevel
from rics.utility.collections import dicts

if TYPE_CHECKING:
    from rics.translation._translator import Translator

FetcherFactory = Callable[[str, Dict[str, Any]], fetching.AbstractFetcher]
"""A callable which creates new ``AbstractFetcher`` instances from a dict config.

Config format is described in :ref:`translator-config-fetching`.

Args:
    clazz: Type of ``AbstractFetcher`` to create.
    config: Keyword arguments for the fetcher class.

Returns:
    A ``Fetcher`` instance.

Raises:
    exceptions.ConfigurationError: If `config` is invalid.
    TypeError: If `clazz` is not an AbstractFetcher subtype.
"""

MapperFactory = Callable[[Dict[str, Any], bool], Optional[_Mapper]]
"""A callable which creates new ``Mapper`` instances from a dict config.

Config format is described in :ref:`translator-config-mapping`.

If ``None`` is returned, a suitable default is used instead.

Args:
    config: Keyword arguments for the ``Mapper``.
    for_fetcher: Flag indicating that the ``Mapper`` returned will be used by an ``AbstractFetcher`` instance.

Returns:
    A ``Mapper`` instance or ``None``.

Raises:
    ConfigurationError: If `config` is invalid.
"""


def default_fetcher_factory(clazz: str, config: Dict[str, Any]) -> fetching.AbstractFetcher:
    """Create an ``AbstractFetcher`` from config."""
    fetcher_class = misc.get_by_full_name(clazz, default_module=fetching)
    fetcher = fetcher_class(**config)
    if not isinstance(fetcher, fetching.AbstractFetcher):
        raise TypeError(f"Fetcher of type {fetcher} created from '{clazz}' is not an AbstractFetcher.")
    return fetcher


def default_mapper_factory(config: Dict[str, Any], for_fetcher: bool) -> Optional[_Mapper]:
    """Create a ``Mapper`` from config."""
    if "score_function" in config and isinstance(config["score_function"], dict):
        score_function = config.pop("score_function")

        if len(score_function) > 1:
            raise exceptions.ConfigurationError(
                f"At most one score function may be specified, but got: {sorted(score_function)}"
            )

        score_function, score_function_kwargs = next(iter(score_function.items()))
        config["score_function"] = score_function
        config["score_function_kwargs"] = score_function_kwargs

    if "score_function_heuristics" in config:
        if "score_function" not in config:
            raise exceptions.ConfigurationError(
                "Section 'score_function_heuristics' requires an explicit score function."
            )

        heuristics = [
            (heuristic_config.pop("function"), heuristic_config)
            for heuristic_config in config.pop("score_function_heuristics")
        ]
        if isinstance(config["score_function"], _HeuristicScore):
            for h in heuristics:
                config["score_function"].add_heuristic(*h)
        else:
            config["score_function"] = _HeuristicScore(config["score_function"], heuristics)

    if "filter_functions" in config:
        filters = config.pop("filter_functions")

        if len(filters) == 1 and filters[0] == {}:
            pass  # Allow/ignore empty section
        else:
            config["filter_functions"] = [(f.pop("function"), f) for f in filters]

    if "overrides" in config:
        overrides = config.pop("overrides")
        shared, specific = _split_overrides(overrides)

        if specific and not for_fetcher:
            raise exceptions.ConfigurationError(
                "Context-sensitive overrides are not possible (or needed) for "
                f"Name-to-source mapping, but got {overrides=}."
            )

        config["overrides"] = dicts.InheritedKeysDict(specific, default=shared) if for_fetcher else shared

    return _Mapper(**config)


class TranslatorFactory(_Generic[NameType, SourceType, IdType]):
    """Create a ``Translator`` from TOML inputs."""

    FETCHER_FACTORY: FetcherFactory = default_fetcher_factory
    """A callable taking (name, kwargs) which returns an ``AbstractFetcher``."""
    MAPPER_FACTORY: MapperFactory = default_mapper_factory
    """A callable taking (kwargs) which returns a ``Mapper``."""

    def __init__(
        self,
        file: PathLikeType,
        extra_fetchers: Iterable[PathLikeType],
    ) -> None:
        self.file = str(file)
        self.extra_fetchers = list(map(str, extra_fetchers))
        self.config_string: str = f"Translator.fromConfig('{self.file}', extra_fetchers={self.extra_fetchers})"

    def create(self) -> "Translator":
        """Create a ``Translator`` from a TOML file."""
        from rics.translation import Translator

        config: Dict[str, Any] = toml.load(self.file)

        _check_allowed_keys(["translator", "mapping", "fetching", "unknown_ids"], config, "<root>")

        translator_config = config.pop("translator", {})

        fetcher = self._handle_fetching(config.pop("fetching", {}), self.extra_fetchers)

        mapper = self._make_mapper("translator", translator_config)
        default_fmt, default_fmt_placeholders = _make_default_translations(**config.pop("unknown_ids", {}))

        return Translator(
            fetcher,
            mapper=mapper,
            default_fmt=default_fmt,
            default_fmt_placeholders=default_fmt_placeholders,
            **translator_config,
        )

    def _handle_fetching(
        self,
        config: Dict[str, Any],
        extra_fetchers: Iterable[str],
    ) -> fetching.Fetcher:
        fetchers = []
        if config:
            fetchers.append(self._make_fetcher(**config))  # Add primary fetcher

        fetchers.extend(
            self._make_fetcher(**toml.load(file_fetcher_file)["fetching"]) for file_fetcher_file in extra_fetchers
        )
        if not fetchers:
            raise exceptions.ConfigurationError(
                "Section [fetching] is required when no pre-initialized AbstractFetcher is given."
            )

        return (
            fetchers[0]
            if len(fetchers) == 1
            else fetching.MultiFetcher(*fetchers, duplicate_source_discovered_action=_ActionLevel.WARN)
        )

    @classmethod
    def _make_mapper(cls, parent_section: str, config: Dict[str, Any]) -> Optional[_Mapper]:
        if "mapping" not in config:
            return None

        config = config.pop("mapping")
        for_fetcher = parent_section.startswith("fetching")
        if for_fetcher:
            config = {**fetching.AbstractFetcher.default_mapper_kwargs(), **config}

        return TranslatorFactory.MAPPER_FACTORY(config, for_fetcher)

    @classmethod
    def _make_fetcher(cls, **config: Any) -> fetching.AbstractFetcher:
        mapper = cls._make_mapper("fetching", config) if "mapping" in config else None

        if len(config) == 0:
            raise exceptions.ConfigurationError("Fetcher implementation section missing.")
        if len(config) > 1:
            raise exceptions.ConfigurationError(
                f"Multiple fetcher implementations specified in the same file: {sorted(config)}"
            )

        clazz, kwargs = next(iter(config.items()))
        kwargs["mapper"] = mapper
        return TranslatorFactory.FETCHER_FACTORY(clazz, kwargs)


def _make_default_translations(**config: Any) -> Tuple[str, Optional[dicts.InheritedKeysDict]]:
    _check_allowed_keys(["fmt", "overrides"], config, toml_path="translator.unknown_ids")

    fmt = config.pop("fmt", None)
    if "overrides" in config:
        shared, specific = _split_overrides(config.pop("overrides"))
        return fmt, dicts.InheritedKeysDict(specific, default=shared)
    else:
        return fmt, None


def _check_forbidden_keys(forbidden: Union[str, Iterable[str]], actual: Iterable[str], toml_path: str) -> None:
    if isinstance(forbidden, str):
        forbidden = [forbidden]

    bad_keys = set(forbidden).intersection(actual)
    if bad_keys:
        raise ValueError(f"Forbidden keys {sorted(bad_keys)} in [{toml_path}]-section.")


def _check_allowed_keys(allowed: Iterable[str], actual: Iterable[str], toml_path: str) -> None:
    if isinstance(allowed, str):
        allowed = [allowed]

    bad_keys = set(actual).difference(allowed)
    if bad_keys:
        raise ValueError(f"Forbidden keys {sorted(bad_keys)} in [{toml_path}]-section.")


def _split_overrides(overrides: dicts.MakeType):  # noqa: ANN202
    specific = {k: v for k, v in overrides.items() if isinstance(v, dict)}
    shared = {k: v for k, v in overrides.items() if k not in specific}
    return shared, specific
