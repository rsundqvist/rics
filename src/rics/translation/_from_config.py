import warnings
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, Optional, Tuple, Type, TypeVar, Union

import toml

from rics.mapping import Mapper
from rics.translation import fetching
from rics.translation.exceptions import ConfigurationError
from rics.translation.offline import DefaultTranslations, PlaceholderOverrides

if TYPE_CHECKING:
    from rics.translation._translator import Translator  # pragma: no cover

FetcherFactory = Callable[[str, Dict[str, Any]], fetching.Fetcher]
MakeFetcherType = Union[fetching.Fetcher, FetcherFactory]
MapperFactory = Callable[[Dict[str, Any]], Mapper]
MakeMapperType = Union[Mapper, MapperFactory]

T = TypeVar("T", DefaultTranslations, PlaceholderOverrides)


def default_fetcher_factory(name: str, kwargs: Dict[str, Any]) -> fetching.Fetcher:
    """Create a Fetcher from a dict config."""
    fetcher_clazz = getattr(fetching, name, None)
    if fetcher_clazz is None:
        raise ValueError(f"Fetcher class '{name}' not known. Consider using the 'fetcher_factory' argument.")
    fetcher = fetcher_clazz(**kwargs)
    if not isinstance(fetcher, fetching.Fetcher):
        raise TypeError(fetcher)
    return fetcher


def default_mapper_factory(config: Dict[str, Any]) -> Mapper:
    """Create a Mapper from a dict config."""
    if not config:
        return Mapper()

    _check_forbidden_keys(["candidates", "cardinality"], config, "fetcher.mapping")

    if "score_function" in config:
        score_function = config.pop("score_function")

        if len(score_function) > 1:
            raise ConfigurationError(f"At most one score function may be specified, but got: {sorted(score_function)}")

        score_function, score_function_kwargs = next(iter(score_function.items()))
        config["score_function"] = score_function
        config.update(score_function_kwargs)

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
        mapper_factory: A pre-initialized Mapper, or a callable taking (kwargs) which returns a Mapper.

    Returns:
        A Translator object.

    Raises:
        ConfigurationError: If the config is invalid.

    Warnings:
        UserWarning: If the user may be doing something they didn't intend to.
    """
    config: Dict[str, Any] = toml.load(file)

    _check_allowed_keys(["translator", "mapping", "fetching", "unknown_ids"], config, "<root>")

    translator_config = config.pop("translator", {})
    fetcher = _make_fetcher(fetcher_factory, **config.pop("fetching", {}))
    mapper = _make_mapper(mapper_factory, translator_config)
    default_fmt, default_translations = _make_default_translations(**config.pop("unknown_ids", {}))

    from rics.translation import Translator

    return Translator(
        fetcher, mapper=mapper, default_translations=default_translations, default_fmt=default_fmt, **translator_config
    )


def _make_default_translations(**config: Any) -> Tuple[str, Optional[DefaultTranslations]]:
    _check_allowed_keys(["fmt", "overrides"], config, toml_path="translator.unknown_ids")
    return (
        config.pop("fmt", None),
        _create_overrides(config["overrides"], DefaultTranslations) if "overrides" in config else None,
    )


def _make_mapper(mapper_factory: MakeMapperType, config: Dict[str, Any]) -> Optional[Mapper]:
    if isinstance(mapper_factory, Mapper):
        if "mapping" in config and mapper_factory != default_mapper_factory:
            warnings.warn(
                "Section [translator.mapping] in the configuration is ignored since a pre-initialized Mapper was given."
            )
        return mapper_factory

    if "mapping" not in config:
        return None

    return mapper_factory(config.pop("mapping"))


def _make_fetcher(factory: MakeFetcherType, **config: Any) -> fetching.Fetcher:
    if isinstance(factory, fetching.Fetcher):
        return factory
    elif not config:
        raise ConfigurationError("Section [fetching] is required when no pre-initialized Fetcher is given.")

    overrides: Optional[PlaceholderOverrides]
    if "mapping" in config:
        mapping = config.pop("mapping")
        _check_allowed_keys("overrides", mapping, toml_path="fetching.mapping")
        overrides = _create_overrides(mapping.pop("overrides", {}), PlaceholderOverrides)
    else:
        overrides = None

    if len(config) == 0:
        raise ConfigurationError("Fetcher implementation section missing.")
    if len(config) > 1:
        raise ConfigurationError(f"Multiple fetcher implementations specified: {sorted(config)}.")

    clazz, kwargs = next(iter(config.items()))
    _check_forbidden_keys(
        ["mapping", "overrides", "placeholder_overrides"], kwargs, toml_path=f"fetching.{clazz}"
    )  # No algorithmic matching yet
    kwargs["placeholder_overrides"] = overrides
    return factory(clazz, kwargs)


def _create_overrides(dict_config: Dict[str, Any], clazz: Type[T]) -> T:
    shared: Dict[str, Any] = {}
    source_specific: Dict[str, Dict[str, Any]] = {}

    for outer_key, outer_value in dict_config.items():
        if isinstance(outer_value, dict):
            for k, v in outer_value.items():
                if outer_key not in source_specific:
                    source_specific[outer_key] = {}
                source_specific[outer_key][k] = v
        else:
            shared[outer_key] = outer_value

    return clazz(shared=shared, source_specific=source_specific)


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
