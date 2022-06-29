"""Factory functions for translation classes."""

from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, Optional, Tuple, Union

import toml

from rics.mapping import HeuristicScore, Mapper
from rics.translation import fetching
from rics.translation.exceptions import ConfigurationError
from rics.translation.fetching import AbstractFetcher, MultiFetcher
from rics.translation.fetching.types import Fetcher
from rics.utility.collections import InheritedKeysDict
from rics.utility.collections.inherited_keys_dict import DefaultType, MakeDict, SpecificType

if TYPE_CHECKING:
    from rics.translation._translator import Translator

FetcherFactory = Callable[[str, Dict[str, Any]], AbstractFetcher]
MakeFetcherType = Union[Fetcher, FetcherFactory]
MapperFactory = Callable[[Dict[str, Any], bool], Optional[Mapper]]
MakeMapperType = Union[Mapper, MapperFactory]


def default_fetcher_factory(clazz: str, config: Dict[str, Any]) -> AbstractFetcher:
    """Create a Fetcher from a dict config.

    Args:
        clazz: Type of Fetcher to create.
        config: Keyword arguments for the fetcher.

    Returns:
        An AbstractFetcher instance.

    Raises:
        ConfigurationError: If `config` is invalid.
        TypeError: If `clazz` is not an AbstractFetcher subtype.
    """
    fetcher_clazz = getattr(fetching, clazz, None)
    if fetcher_clazz is None:
        raise ConfigurationError(
            f"Fetcher class '{clazz}' not known. Use the 'fetcher_factory' argument "
            "to initialize customer implementations."
        )
    fetcher = fetcher_clazz(**config)
    if not isinstance(fetcher, AbstractFetcher):
        raise TypeError(fetcher)
    return fetcher


def default_mapper_factory(config: Dict[str, Any], for_fetcher: bool) -> Optional[Mapper]:
    """Create a Mapper from a dict config.

    Args:
        config: Keyword arguments for the fetcher.
        for_fetcher: Flag indicating that the mapper returned will be used by an AbstractFetcher instance.

    Returns:
        A Mapper instance.

    Raises:
        ConfigurationError: If `config` is invalid.
    """
    if "score_function" in config and isinstance(config["score_function"], dict):
        score_function = config.pop("score_function")

        if len(score_function) > 1:
            raise ConfigurationError(f"At most one score function may be specified, but got: {sorted(score_function)}")

        score_function, score_function_kwargs = next(iter(score_function.items()))
        config["score_function"] = score_function
        config["score_function_kwargs"] = score_function_kwargs

    if "score_function_heuristics" in config:
        if "score_function" not in config:
            raise ConfigurationError("Section 'score_function_heuristics' requires an explicit score function.")

        heuristics = [
            (heuristic_config.pop("function"), heuristic_config)
            for heuristic_config in config.pop("score_function_heuristics")
        ]
        if isinstance(config["score_function"], HeuristicScore):
            for h in heuristics:
                config["score_function"].add_heuristic(*h)
        else:
            config["score_function"] = HeuristicScore(config["score_function"], heuristics)

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
            raise ConfigurationError(
                "Context-sensitive overrides are not possible (or needed) for "
                f"Name-to-source mapping, but got {overrides=}."
            )

        config["overrides"] = InheritedKeysDict(specific, default=shared) if for_fetcher else shared

    return Mapper(**config)


def translator_from_toml_config(
    file: str,
    extra_fetchers: Iterable[str] = (),
    /,
    fetcher_factory: MakeFetcherType = default_fetcher_factory,
    mapper_factory: MakeMapperType = default_mapper_factory,
) -> "Translator":
    """Create a translator from a TOML file.

    Args:
        file: Path to a TOML file, or a pre-parsed dict.
        extra_fetchers: Path to TOML files defining additional fetchers. Useful for fetching from multiple sources or
            kinds of sources, for example locally stored files in conjunction with one or more databases. The fetchers
            are ranked by input order, with the fetcher defined in `file` being given the highest priority (rank 0).
        fetcher_factory: A Fetcher instance, or a callable taking (name, kwargs) which returns an AbstractFetcher.
        mapper_factory: A Mapper instance, or a callable taking (kwargs) which returns a Mapper. Used for both
            Translator and Fetcher mapper initialization.

    Returns:
        A Translator object.

    Raises:
        ConfigurationError: If the config is invalid.

    Warnings:
        UserWarning: If the user may be doing something they didn't intend to.
    """
    from rics.translation import Translator

    config: Dict[str, Any] = toml.load(file)

    _check_allowed_keys(["translator", "mapping", "fetching", "unknown_ids"], config, "<root>")

    translator_config = config.pop("translator", {})

    fetcher = _handle_fetching(config.pop("fetching", {}), extra_fetchers, fetcher_factory, mapper_factory)

    mapper = _make_mapper("translator", mapper_factory, translator_config)
    default_fmt, default_translations = _make_default_translations(**config.pop("unknown_ids", {}))

    return Translator(
        fetcher, mapper=mapper, default_translations=default_translations, default_fmt=default_fmt, **translator_config
    )


def _handle_fetching(
    config: Dict[str, Any],
    extra_fetchers: Iterable[str],
    fetcher_factory: MakeFetcherType,
    mapper_factory: MakeMapperType,
) -> Fetcher:
    if isinstance(fetcher_factory, Fetcher):
        if extra_fetchers:
            raise ConfigurationError(f"Cannot pass a Fetcher as 'fetcher_factory' with {extra_fetchers=}.")
        if config:
            raise ConfigurationError("Pre-initialized Fetcher given; section [fetching] redundant.")
        return fetcher_factory

    fetchers = []
    if config:
        fetchers.append(_make_fetcher(fetcher_factory, mapper_factory, **config))  # Add primary fetcher

    fetchers.extend(
        _make_fetcher(fetcher_factory, mapper_factory, **toml.load(file_fetcher_file)["fetching"])
        for file_fetcher_file in extra_fetchers
    )
    if not fetchers:
        raise ConfigurationError("Section [fetching] is required when no pre-initialized AbstractFetcher is given.")

    return fetchers[0] if len(fetchers) == 1 else MultiFetcher(*fetchers, duplicate_source_discovered_action="warn")


def _make_default_translations(**config: Any) -> Tuple[str, Optional[InheritedKeysDict]]:
    _check_allowed_keys(["fmt", "overrides"], config, toml_path="translator.unknown_ids")

    fmt = config.pop("fmt", None)
    if "overrides" in config:
        shared, specific = _split_overrides(config.pop("overrides"))
        return fmt, InheritedKeysDict(specific, default=shared)
    else:
        return fmt, None


def _make_mapper(parent_section: str, mapper_factory: MakeMapperType, config: Dict[str, Any]) -> Optional[Mapper]:
    if isinstance(mapper_factory, Mapper):
        if "mapping" in config:
            raise ConfigurationError(f"Pre-initialized Mapper given; section [{parent_section}.mapping] redundant.")
        return mapper_factory

    if "mapping" not in config:
        return None

    config = config.pop("mapping")
    for_fetcher = parent_section.startswith("fetching")
    if for_fetcher:
        config = {**AbstractFetcher.default_mapper_kwargs(), **config}

    _check_forbidden_keys(["value", "candidates"], config, f"{parent_section}.mapping")
    return mapper_factory(config, for_fetcher)


def _make_fetcher(factory: FetcherFactory, mapper_factory: MakeMapperType, **config: Any) -> Fetcher:
    mapper = _make_mapper("fetching", mapper_factory, config) if "mapping" in config else None

    if len(config) == 0:
        raise ConfigurationError("Fetcher implementation section missing.")
    if len(config) > 1:
        raise ConfigurationError(f"Multiple fetcher implementations specified in the same file: {sorted(config)}")

    clazz, kwargs = next(iter(config.items()))
    kwargs["mapper"] = mapper
    return factory(clazz, kwargs)


def _split_overrides(overrides: MakeDict) -> Tuple[DefaultType, SpecificType]:
    specific = {k: v for k, v in overrides.items() if isinstance(v, dict)}
    shared = {k: v for k, v in overrides.items() if k not in specific}
    return shared, specific


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
