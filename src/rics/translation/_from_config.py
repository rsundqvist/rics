from typing import TYPE_CHECKING, Any, Dict, Union

import yaml

from rics._internal_support.types import PathLikeType
from rics.mapping import Mapper
from rics.translation.exceptions import ConfigurationError
from rics.translation.fetching import Fetcher, PandasFetcher, SqlFetcher
from rics.translation.offline import PlaceholderOverrides
from rics.utility.misc import tname

if TYPE_CHECKING:
    from rics.translation._translator import Translator  # pragma: no cover


def translator_from_yaml_config(path: Union[PathLikeType, Dict[str, Any]]) -> "Translator":
    """Create a translator from a YAML file.

    Args:
        path: Path to a YAML file, or a pre-parsed dict.

    Returns:
        A Translator object.

    Raises:
        ConfigurationError: If the config is invalid.
    """
    if isinstance(path, dict):
        config = path  # pragma: no cover
    else:
        with open(path) as f:
            config = yaml.safe_load(f)

    try:
        return _parse(config)
    except Exception as e:  # noqa: B902, pragma: no cover
        raise ConfigurationError(f"{e}, {path=}") from e


def _parse(config: Dict[str, Any]) -> "Translator":
    main = config.pop("translator")
    fetcher = config.pop("fetcher")
    mapper = _make_mapper(**config.pop("name-to-source-mapping", {}))
    placeholder_overrides = PlaceholderOverrides.from_dict(config.pop("placeholder-overrides", {}))
    default_translations = config.pop("default-translations", None)

    if config:
        raise ConfigurationError(f"Invalid configuration. Unknown keys: {list(config)}")

    fetcher = _make_fetcher(fetcher, placeholder_overrides)

    from rics.translation._translator import Translator

    return Translator(fetcher, **main, mapper=mapper, default_translations=default_translations)


def _make_mapper(**config: Any) -> Mapper:
    if "score-function" in config:  # pragma: no cover
        score_function = config.pop("score-function")
        config["score_function"] = score_function.pop("name")
        config.update(**score_function)

    return Mapper.from_dict(config)


def _make_fetcher(base_config: Dict[str, Any], placeholder_overrides: PlaceholderOverrides) -> "Fetcher":
    name = base_config.pop("class")

    clazz = None
    if "." not in name:
        for candidate in (PandasFetcher, SqlFetcher):
            if tname(candidate) == name:
                clazz = candidate
    else:
        raise NotImplementedError("TODO: Custom fetcher class loading with YAML.")

    if clazz is None:
        raise ValueError(f"Could not find a fetcher class with {name=}.")  # pragma: no cover

    class_specific_kwargs = base_config.pop("class-specific-kwargs", {})
    return clazz(**base_config, **class_specific_kwargs, placeholder_overrides=placeholder_overrides)
