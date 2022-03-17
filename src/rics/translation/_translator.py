import logging
import warnings
from collections import defaultdict
from typing import Any, Callable, Dict, Generic, Iterable, List, Optional, Set, Type, Union

from rics._internal_support.types import PathLikeType
from rics.mapping import DirectionalMapping, Mapper
from rics.mapping.exceptions import MappingError
from rics.translation._from_config import translator_from_yaml_config as _from_config
from rics.translation.dio import DataStructureIO, DefaultTranslatable, resolve_io
from rics.translation.exceptions import OfflineError
from rics.translation.fetching import Fetcher
from rics.translation.fetching._ids_to_fetch import IdsToFetch
from rics.translation.offline import Format, TranslationMap
from rics.translation.offline.types import IdType, NameType, SourcePlaceholderTranslations, SourceType
from rics.utility.misc import tname

_NAME_ATTRIBUTES = ("keys", "name", "names", "columns")

LOGGER = logging.getLogger(__package__).getChild("Translator")

NamesPredicate = Callable[[NameType], bool]
NameTypes = Union[NameType, Iterable[NameType]]
Names = Union[NameTypes, NamesPredicate]


class Translator(Generic[DefaultTranslatable, NameType, IdType, SourceType]):
    """Translate IDs to human-readable labels.

    Args:
        fetcher: A :class:`~rics.translation.fetching.Fetcher` or ready-to-use translations.
        fmt: String :class:`~rics.translation.offline.Format` for translations.
        mapper: A :class:`~rics.mapping.Mapper` instance for binding names to sources.
        default_translations: Shared and/or source-specific default placeholder values.

    See Also:
        Related classes:

        * :class:`rics.translation.offline.Format`, the format specification.
        * :class:`rics.translation.offline.TranslationMap`, application of formats.
        * :class:`rics.translation.fetching.Fetcher`, fetching of translation data from external sources.
    """

    @classmethod
    def from_config(cls, path: Union[PathLikeType, Dict[str, Any]]) -> "Translator":
        """Create a translator from a YAML file.

        Args:
            path: Path to a YAML file, or a pre-parsed dict.

        Returns:
            A Translator object.

        Raises:
            ConfigurationError: If the config is invalid.
        """
        return _from_config(path)

    def __init__(
        self,
        fetcher: Union[Fetcher, TranslationMap, SourcePlaceholderTranslations],
        fmt: Union[str, Format] = "{id}:{name}",
        mapper: Mapper = None,
        default_translations: Dict[SourceType, Dict[str, Any]] = None,
    ) -> None:
        self._fmt = fmt if isinstance(fmt, Format) else Format(fmt)
        self._mapper = mapper or Mapper()
        self._default: Optional[Dict[SourceType, Dict[str, Any]]] = default_translations

        self._cached_tmap: Optional[TranslationMap]
        if isinstance(fetcher, Fetcher):
            self._fetcher = fetcher
            self._cached_tmap = None
        else:  # pragma: no cover
            self._cached_tmap = self._to_translation_map(fetcher) if isinstance(fetcher, dict) else fetcher

    def translate(
        self,
        translatable: DefaultTranslatable,
        names: Names = None,
        ignore_names: Names = None,
        inplace: bool = False,
    ) -> Optional[DefaultTranslatable]:
        """Translate IDs to human-readable strings.

        Args:
            translatable: A data structure to translate.
            names: Explicit names to translate. Will try to derive form `translatable` if not given. May also be a
                predicate which indicates (returns True for) derived names to keep.
            ignore_names: Names **not** to translate. Always precedence over `names`, both explicit and derived. May
                also be a predicate which indicates (returns True for) names to ignore.
            inplace: If True, translation is performed in-place and this function returns None.

        Returns:
            A copy of `translatable` with IDs replaced by translations if ``inplace=False``, otherwise None.

        Raises:
            UntranslatableTypeError: If `translatable` is not translatable using any standard IOs.
            AttributeError: If `names` are not given and cannot be derived from `translatable`.
            MappingError: If required (explicitly given) names fail to map to a source.
        """
        translatable_io = resolve_io(translatable)  # Fail fast if untranslatable type

        name_to_source = self.map_to_sources(translatable, names, ignore_names)
        if name_to_source is None:
            return None if inplace else translatable  # pragma: no cover

        # Get translations
        if self._cached_tmap is None:  # Fetch new data
            source_placeholder_translations = self._fetch(
                self._get_ids_to_fetch(name_to_source, translatable, translatable_io)
            )
            tmap = self._to_translation_map(source_placeholder_translations)
        else:  # Use cached
            tmap = self._cached_tmap

        # Update
        tmap.name_to_source = name_to_source.flatten()

        return translatable_io.insert(translatable, tmap=tmap, copy=not inplace)

    def map_to_sources(
        self,
        translatable: DefaultTranslatable,
        names: Names = None,
        ignore_names: Names = None,
    ) -> Optional[DirectionalMapping]:
        """Map names to translation sources.

        Args:
            translatable: A data structure to map names for.
            names: Explicit names to translate. Will try to derive form `translatable` if not given. May also be a
                predicate which indicates (returns True for) derived names to keep.
            ignore_names: Names **not** to translate. Always precedence over `names`, both explicit and derived. May
                also be a predicate which indicates (returns True for) names to ignore.

        Returns:
            A mapping of names to translation sources. Returns None if mapping failed but success was not required.

        Raises:
            AttributeError: If `names` are not given and cannot be derived from `translatable`.
            MappingError: If required (explicitly given) names fail to map to a source.
        """
        # Get names and figure out where to get them from
        names_to_translate = self._resolve_names(translatable, names, ignore_names)

        if self.online:
            sources = self._fetcher.sources
        elif self._cached_tmap is not None:
            sources = list(self._cached_tmap.keys())
        else:
            raise AssertionError("This should be impossible.")

        self._mapper.candidates = set(sources)
        name_to_source = self._mapper.apply(names_to_translate)

        # Fail if any of the explicitly given (ie literal, not predicate) names fail to map to a source.
        if isinstance(names, (str, Iterable)):
            required = set(self._dont_ruin_string(names))
            unmapped = required.difference(name_to_source.left)
            if unmapped:
                raise MappingError(f"Required names {unmapped} not mapped with {sources=} and {ignore_names=}.")

        if not name_to_source.left:
            msg = f"None of {names=} could not be mapped with {sources=}. Translation aborted"
            warnings.warn(msg)
            return None

        return name_to_source

    @property
    def online(self) -> bool:
        """Return connectivity status. If False, no new translations may be fetched."""
        return hasattr(self, "_fetcher")

    def store(self, delete_fetcher: bool = True) -> TranslationMap:
        """Retrieve and store as many translations as possible.

        Args:
            delete_fetcher: If True, go offline after retrieving data. The translation will still function, but some
                methods may raise exceptions and new data cannot be retrieved. Deleting allows the fetcher to close
                files and connections. If the fetcher has a ``close()``-method, it will be called before deletion.

        Returns:
            A mapping for translation. This instance is kept by the translator to continue operation offline, and the
            map may be modified by this process. use ``copy()`` on the map to ensure immutability.

        Raises:
            ForbiddenOperationError: If the fetcher does not permit this operation.

        See Also:
            :meth:`rics.translation.fetching.Fetcher.fetch_all`
            :class:`rics.translation.offline.TranslationMap`
        """
        source_placeholder_translations: SourcePlaceholderTranslations = self._fetch(None)

        translation_map = self._to_translation_map(source_placeholder_translations)
        LOGGER.info("Store %s", translation_map)
        if delete_fetcher:  # pragma: no cover
            self._fetcher.close()
            del self._fetcher
        self._cached_tmap = translation_map
        return translation_map

    @staticmethod
    def _get_ids_to_fetch(
        name_to_source: DirectionalMapping,
        translatable: DefaultTranslatable,
        dio: Type[DataStructureIO],
    ) -> List[IdsToFetch]:

        # Aggregate and remove duplicates.
        source_to_ids: Dict[SourceType, Set[IdType]] = defaultdict(set)
        for name, ids in dio.extract(translatable, list(name_to_source.left)).items():
            source_to_ids[name_to_source.left_to_right[name][0]].update(ids)  # type: ignore

        return [IdsToFetch(source, ids) for source, ids in source_to_ids.items()]

    def _fetch(self, ids_to_fetch: Optional[List[IdsToFetch]]) -> SourcePlaceholderTranslations:
        if not self.online:
            raise OfflineError("Cannot fetch new translations.")  # pragma: no cover

        placeholders = self._fmt.placeholders
        required = self._fmt.required_placeholders
        return (
            self._fetcher.fetch_all(placeholders, required)
            if ids_to_fetch is None
            else self._fetcher.fetch(ids_to_fetch, placeholders, required)
        )

    def _to_translation_map(self, source_placeholder_translations: SourcePlaceholderTranslations) -> TranslationMap:
        return TranslationMap(
            source_placeholder_translations,
            None,
            self._fmt,
            self._default,
        )

    def __repr__(self) -> str:
        more = f"fetcher={self._fetcher}" if self.online else f"cache={self._cached_tmap}"

        online = self.online
        return f"{tname(self)}({online=}: {more})"

    def _resolve_names(
        self,
        translatable: DefaultTranslatable,
        names: Optional[Names],
        ignored_names: Optional[Names],
    ) -> List[NameType]:

        found_names: NameTypes
        if names is None or callable(names):
            found_names = self._extract_from_attribute(translatable)
            if callable(names):
                keep_predicate: NamesPredicate = names
                found_names = list(filter(keep_predicate, found_names))
        else:
            found_names = self._dont_ruin_string(names)

        names_to_translate: List[NameType] = self._resolve_names_inner(
            names=found_names,
            ignored_names=ignored_names if callable(ignored_names) else set(self._dont_ruin_string(ignored_names)),
        )
        return names_to_translate

    @staticmethod
    def _extract_from_attribute(translatable: DefaultTranslatable) -> List[NameType]:
        for attr_name in _NAME_ATTRIBUTES:
            if hasattr(translatable, attr_name):
                attr = getattr(translatable, attr_name)
                return list(attr() if callable(attr) else attr)

        raise AttributeError(
            "Must pass 'names' since type " f"'{type(translatable)}' has none of {_NAME_ATTRIBUTES} as and attribute."
        )

    @staticmethod
    def _resolve_names_inner(
        names: List[NameType], ignored_names: Union[NamesPredicate, Set[NameType]]
    ) -> List[NameType]:
        predicate = _IgnoredNamesPredicate(ignored_names).apply
        names_to_translate = list(filter(predicate, names))
        if not names_to_translate and names:
            warnings.warn(f"No names left to translate. Ignored names: {ignored_names}, explicit names: {names}.")
        return names_to_translate

    @staticmethod
    def _dont_ruin_string(arg: Optional[NameTypes]) -> List[NameType]:
        if arg is None:
            return []
        if not isinstance(arg, str) and isinstance(arg, Iterable):
            return list(arg)

        # https://github.com/python/mypy/issues/10835
        return [arg]  # type: ignore


class _IgnoredNamesPredicate(Generic[NameType]):
    def __init__(self, ignored_names: Union[NamesPredicate, Set[NameType]]) -> None:
        self._func = ignored_names if callable(ignored_names) else ignored_names.__contains__

    def apply(self, name: NameType) -> bool:
        return not self._func(name)
