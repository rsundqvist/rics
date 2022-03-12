import logging
import warnings
from collections import defaultdict
from typing import Any, Dict, Generic, Iterable, List, Optional, Set, Tuple, Type, Union

from rics._internal_support.types import PathLikeType
from rics.mapping import DirectionalMapping, Mapper
from rics.mapping.exceptions import MappingError
from rics.translation._from_config import translator_from_yaml_config as _from_config
from rics.translation.dio import DataStructureIO, DefaultTranslatable, resolve_io
from rics.translation.fetching import Fetcher
from rics.translation.fetching._ids_to_fetch import IdsToFetch
from rics.translation.offline import Format, TranslationMap
from rics.translation.offline.exceptions import OfflineError
from rics.translation.offline.types import IdType, NameType, SourcePlaceholdersDict, SourceType
from rics.utility.misc import tname

_NAME_ATTRIBUTES = ("keys", "name", "names", "columns")

LOGGER = logging.getLogger(__package__).getChild("Translator")


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
    def from_config(cls, path: PathLikeType) -> "Translator":
        """Create a translator from a YAML file.

        Args:
            path: Path to a YAML file.

        Returns:
            A Translator object.

        Raises:
            ConfigurationError: If the config is invalid.
        """
        return _from_config(path)

    def __init__(
        self,
        fetcher: Union[Fetcher, TranslationMap, SourcePlaceholdersDict],
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
        names: Union[NameType, Iterable[NameType]] = None,
        ignore_names: Union[NameType, Iterable[NameType]] = None,
        inplace: bool = False,
    ) -> Optional[DefaultTranslatable]:
        """Translate IDs to human-readable strings.

        Args:
            translatable: A data structure to translate.
            names: Explicit names to translate. Will try to derive form `translatable` if not given.
            ignore_names: Names **not** to translate. Always precedence over `names`, both explicit and derived.
            inplace: If True, translation is performed in-place and this function returns None.

        Returns:
            A copy of `translatable` with IDs replaced by translations if ``inplace=False``, otherwise None.

        Raises:
            UntranslatableTypeError: If `translatable` is not translatable using any standard IOs.
            AttributeError: If `names` are not given and cannot be derived from `translatable`.
            AttributeError: If `names` are not given and cannot be derived from `translatable`.
            MappingError: If required (explicitly given) names fail to map to a source.
        """
        translatable_io = resolve_io(translatable)  # Fail fast if untranslatable type

        # Get names and figure out where to get them from
        names, required = self._resolve_names(translatable, names, ignore_names)

        if self.online:
            sources = self._fetcher.sources
        elif self._cached_tmap is not None:
            sources = list(self._cached_tmap.keys())
        else:
            raise AssertionError("This should be impossible.")

        self._mapper.candidates = set(sources)
        name_to_source = self._mapper.apply(names)

        # Fail if any of the explicitly given names fail to map to a source.
        if required:
            unmapped_required = set(names).difference(name_to_source.left)
            if unmapped_required:
                raise MappingError(f"Required names {unmapped_required} not mapped with {sources=}.")

        if not name_to_source.left:
            msg = f"None of {names=} could not be mapped with {sources=}."
            warnings.warn(msg)
            return None if inplace else translatable

        # Get translations
        if self._cached_tmap is None:  # Fetch new data
            source_placeholders_dict = self._fetch(
                self._get_ids_to_fetch(name_to_source, translatable, translatable_io)
            )
            tmap = self._to_translation_map(source_placeholders_dict)
        else:  # Use cached
            tmap = self._cached_tmap

        # Update
        tmap.name_to_source = name_to_source.flatten()

        return translatable_io.insert(translatable, names=names, tmap=tmap, copy=not inplace)

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
        source_placeholders_dict: SourcePlaceholdersDict = self._fetch(None)

        translation_map = self._to_translation_map(source_placeholders_dict)
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

    def _fetch(self, ids_to_fetch: Optional[List[IdsToFetch]]) -> SourcePlaceholdersDict:
        if not self.online:
            raise OfflineError("Cannot fetch new translations.")  # pragma: no cover

        required_placeholders = self._fmt.required_placeholders
        optional_placeholders = self._fmt.optional_placeholders
        return (
            self._fetcher.fetch_all(required_placeholders, optional_placeholders)
            if ids_to_fetch is None
            else self._fetcher.fetch(ids_to_fetch, required_placeholders, optional_placeholders)
        )

    def _to_translation_map(self, source_placeholders_dict: SourcePlaceholdersDict) -> TranslationMap:
        return TranslationMap(
            source_placeholders_dict,
            None,
            self._fmt,
            self._default,
        )

    def __repr__(self) -> str:
        more = f"fetcher={self._fetcher}" if self.online else f"cache={self._cached_tmap}"

        online = self.online
        return f"{tname(self)}({online=}: {more})"

    @staticmethod
    def _resolve_names_inner(names: List[NameType], ignored_names: Set[NameType]) -> List[NameType]:
        names_to_translate = list(filter(lambda name: name not in ignored_names, names))
        if not names_to_translate and names:
            warnings.warn(f"No names left to translate. Ignored names: {ignored_names}, explicit names: {names}.")
        return names_to_translate

    def _resolve_names(
        self,
        translatable: DefaultTranslatable,
        names: Optional[Union[NameType, Iterable[NameType]]],
        ignored_names: Optional[Union[NameType, Iterable[NameType]]],
    ) -> Tuple[List[NameType], bool]:
        found_names: Optional[Union[NameType, Iterable[NameType]]] = None
        if names is None:
            found = False
            for attr_name in _NAME_ATTRIBUTES:
                if hasattr(translatable, attr_name):
                    attr = getattr(translatable, attr_name)
                    found_names = list(attr() if callable(attr) else attr)
                    found = True
                    break
            if not found:
                raise AttributeError(
                    "Must pass 'names' since type "
                    f"'{type(translatable)}' has none of {_NAME_ATTRIBUTES} as and attribute."
                )
        else:
            found_names = names

        names_to_translate: List[NameType] = self._resolve_names_inner(
            names=self._dont_ruin_string(found_names),
            ignored_names=set(self._dont_ruin_string(ignored_names)),
        )

        required = names is not None
        return names_to_translate, required

    @staticmethod
    def _dont_ruin_string(arg: Optional[Union[NameType, Iterable[NameType]]]) -> List[NameType]:
        if arg is None:
            return []
        if isinstance(arg, (str, int)):
            return [arg]
        return list(arg)
