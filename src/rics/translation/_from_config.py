import warnings
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, Optional, Tuple, Union

import toml

from rics.mapping import Mapper
from rics.translation import fetching
from rics.translation.exceptions import ConfigurationError
from rics.utility.collections import InheritedKeysDict
from rics.utility.collections.inherited_keys_dict import DefaultType, MakeDict, SpecificType

if TYPE_CHECKING:
    from rics.translation._translator import Translator  # pragma: no cover

FetcherFactory = Callable[[str, Dict[str, Any]], fetching.Fetcher]
MakeFetcherType = Union[fetching.Fetcher, FetcherFactory]
MapperFactory = Callable[[Dict[str, Any], bool], Optional[Mapper]]
MakeMapperType = Union[Mapper, MapperFactory]


def default_fetcher_factory(name: str, kwargs: Dict[str, Any]) -> fetching.Fetcher:
    """Create a Fetcher from a dict config."""
    fetcher_clazz = getattr(fetching, name, None)
    if fetcher_clazz is None:
        raise ValueError(f"Fetcher class '{name}' not known. Consider using the 'fetcher_factory' argument.")
    fetcher = fetcher_clazz(**kwargs)
    if not isinstance(fetcher, fetching.Fetcher):
        raise TypeError(fetcher)
    return fetcher


def default_mapper_factory(config: Dict[str, Any], for_fetcher: bool) -> Optional[Mapper]:
    """Create a Mapper from a dict config."""
    if not config:
        return None

    if "score_function" in config and not isinstance(config["score_function"], str):
        score_function = config.pop("score_function")

        if len(score_function) > 1:
            raise ConfigurationError(f"At most one score function may be specified, but got: {sorted(score_function)}")

        score_function, score_function_kwargs = next(iter(score_function.items()))
        config["score_function"] = score_function
        config["score_function_kwargs"] = score_function_kwargs

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
    fetcher_factory: MakeFetcherType = default_fetcher_factory,
    mapper_factory: MakeMapperType = default_mapper_factory,
) -> "Translator":
    """Create a translator from a TOML file.

    Args:
        file: Path to a TOML file, or a pre-parsed dict.
        fetcher_factory: A pre-initialized Fetcher, or a callable taking (name, kwargs) which returns a Fetcher.
        mapper_factory: A pre-initialized Mapper, or a callable taking (kwargs) which returns a Mapper. Used for both
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
    fetcher = _make_fetcher(fetcher_factory, mapper_factory, **config.pop("fetching", {}))
    mapper = _make_mapper("translator", mapper_factory, translator_config)
    default_fmt, default_translations = _make_default_translations(**config.pop("unknown_ids", {}))

    return Translator(
        fetcher, mapper=mapper, default_translations=default_translations, default_fmt=default_fmt, **translator_config
    )


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
        if "mapping" in config and mapper_factory != default_mapper_factory:
            warnings.warn(
                f"Section [{parent_section}.mapping] in the configuration is "
                f"ignored since a pre-initialized Mapper was given."
            )
        return mapper_factory

    if "mapping" not in config:
        return None

    config = config.pop("mapping")
    for_fetcher = parent_section.startswith("fetching")
    if for_fetcher:
        config = {**fetching.Fetcher.default_mapper_kwargs(), **config}

    _check_forbidden_keys(["candidates", "cardinality"], config, f"{parent_section}.mapping")
    return mapper_factory(config, for_fetcher)


def _make_fetcher(factory: MakeFetcherType, mapper_factory: MakeMapperType, **config: Any) -> fetching.Fetcher:
    if isinstance(factory, fetching.Fetcher):
        return factory
    elif not config:
        raise ConfigurationError("Section [fetching] is required when no pre-initialized Fetcher is given.")

    mapper = _make_mapper("fetching", mapper_factory, config) if "mapping" in config else None

    if len(config) == 0:
        raise ConfigurationError("Fetcher implementation section missing.")
    if len(config) > 1:
        raise ConfigurationError(f"Multiple fetcher implementations specified: {sorted(config)}.")

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
