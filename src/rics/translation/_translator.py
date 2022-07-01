import logging
import warnings
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, Generic, Iterable, List, Optional, Set, Tuple, Type, Union

from rics._internal_support.types import PathLikeType
from rics.mapping import DirectionalMapping, Mapper
from rics.mapping.exceptions import MappingError
from rics.translation import factory
from rics.translation.dio import DataStructureIO, DefaultTranslatable, resolve_io
from rics.translation.exceptions import OfflineError
from rics.translation.fetching.types import Fetcher, IdsToFetch
from rics.translation.offline import Format, TranslationMap
from rics.translation.offline.types import (
    FormatType,
    IdType,
    NameType,
    PlaceholderTranslations,
    SourcePlaceholderTranslations,
    SourceType,
)
from rics.utility.collections.inherited_keys_dict import InheritedKeysDict, MakeDict
from rics.utility.misc import tname

_NAME_ATTRIBUTES = ("name", "names", "columns", "keys")

LOGGER = logging.getLogger(__package__).getChild("Translator")

DEFAULT_STORAGE_PATH = Path("~").joinpath(".rics").joinpath("offline-translator.pkl")

NamesPredicate = Callable[[NameType], bool]
NameTypes = Union[NameType, Iterable[NameType]]
Names = Union[NameTypes, NamesPredicate]


class Translator(Generic[DefaultTranslatable, NameType, IdType, SourceType]):
    """Translate IDs to human-readable labels.

    Untranslatable IDs will be None by default if neither `default_fmt` nor `default_translations` is given.

    Args:
        fetcher: A :class:`.Fetcher` or ready-to-use translations.
        fmt: String :class:`.Format` specification for translations.
        mapper: A :class:`.Mapper` instance for binding names to sources.
        default_fmt: Alternative :class:`.Format` to use instead of `fmt` for fallback translation of unknown IDs.
        default_translations: Shared and/or source-specific default placeholder values for unknown IDs. See the
            :meth:`.InheritedKeysDict.make`-method documentation for details on how to specify these.
    """

    @classmethod
    def from_config(
        cls,
        path: PathLikeType,
        extra_fetchers: Iterable[str] = (),
        /,
        fetcher_factory: factory.MakeFetcherType = factory.default_fetcher_factory,
        mapper_factory: factory.MakeMapperType = factory.default_mapper_factory,
    ) -> "Translator":
        """See :func:`rics.translation.factory.translator_from_toml_config`."""
        return factory.translator_from_toml_config(
            str(path), extra_fetchers, fetcher_factory=fetcher_factory, mapper_factory=mapper_factory
        )

    def __init__(
        self,
        fetcher: Union[
            Fetcher,
            TranslationMap,
            SourcePlaceholderTranslations,
            Dict[SourceType, PlaceholderTranslations.MakeTypes],
        ],
        fmt: FormatType = "{id}:{name}",
        mapper: Mapper = None,
        default_fmt: FormatType = None,
        default_translations: Union[InheritedKeysDict[SourceType, str, Any], MakeDict] = None,
    ) -> None:
        self._fmt = fmt if isinstance(fmt, Format) else Format(fmt)
        self._mapper = mapper or Mapper()
        self._default, self._default_fmt = _handle_default(self._fmt, default_fmt, default_translations)

        self._cached_tmap: TranslationMap
        if isinstance(fetcher, Fetcher):
            self._fetcher = fetcher
            self._cached_tmap = TranslationMap({})
        else:  # pragma: no cover
            self._cached_tmap = (
                self._to_translation_map(
                    {source: PlaceholderTranslations.make(source, pht) for source, pht in fetcher.items()}
                )
                if isinstance(fetcher, dict)
                else fetcher
            )

    def copy(self, share_fetcher: bool = True, **overrides: Any) -> "Translator":
        """Make a copy of this translator.

        Args:
            share_fetcher: If True, the returned translator will share the current translator's fetcher.
            overrides: Keyword arguments to use when instantiating the copy. Options that aren't given will be taken
                from the current instance. See the :class:`Translator` class documentation for possible choices.

        Returns:
            A copy of this translator with `overrides` applied.

        Raises:
            NotImplementedError: If ``share_fetcher=False``.
        """
        if not share_fetcher:
            raise NotImplementedError("Fetcher clone not implemented.")

        kwargs: Dict[str, Any] = {
            "fmt": self._fmt,
            "default_fmt": self._default_fmt,
            **overrides,
        }

        if "mapper" not in kwargs:  # pragma: no cover
            kwargs["mapper"] = self._mapper.copy()

        if "fetcher" not in kwargs:  # pragma: no cover
            kwargs["fetcher"] = self._fetcher if self.online else self._cached_tmap.copy()  # type: ignore

        if "default_translations" not in kwargs:  # pragma: no cover
            kwargs["default_translations"] = self._default

        return Translator(**kwargs)

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
        translation_map, names_to_translate = self._get_updated_tmap(translatable, names, ignore_names=ignore_names)
        if not translation_map:
            return None if inplace else translatable  # pragma: no cover

        return resolve_io(translatable).insert(
            translatable, names=names_to_translate, tmap=translation_map, copy=not inplace
        )

    def __call__(
        self,
        translatable: DefaultTranslatable,
        names: Names = None,
        ignore_names: Names = None,
        inplace: bool = False,
    ) -> Optional[DefaultTranslatable]:
        """Inherits docstring from self.translate."""
        return self.translate(translatable, names, ignore_names, inplace)  # pragma: no cover

    __call__.__doc__ = translate.__doc__

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
        names_to_translate = self._resolve_names(translatable, names, ignore_names)
        sources = self._fetcher.sources if self.online else self._cached_tmap.sources

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

    def fetch(
        self,
        translatable: DefaultTranslatable,
        name_to_source: DirectionalMapping[NameType, SourceType],
        data_structure_io: Type[DataStructureIO] = None,
    ) -> TranslationMap:
        """Fetch translations.

        Args:
            translatable: A data structure to translate.
            name_to_source: Mappings of names in `translatable` to translation sources known the fetcher.
            data_structure_io: Static Data Structure IO class used to extract IDs from `translatable`. None=derive.

        Returns:
            A :class:`.TranslationMap`.

        Raises:
            OfflineError: If disconnected from the fetcher, ie not :attr:`online`.
        """
        ids_to_fetch = self._get_ids_to_fetch(
            name_to_source, translatable, data_structure_io or resolve_io(translatable)
        )
        source_translations = self._fetch(ids_to_fetch)
        return self._to_translation_map(source_translations)

    @property
    def online(self) -> bool:
        """Return connectivity status. If False, no new translations may be fetched."""
        return hasattr(self, "_fetcher")

    @classmethod
    def restore(cls, path: PathLikeType = DEFAULT_STORAGE_PATH) -> "Translator":
        """Restore a serialized Translator.

        Args:
            path: Path to a serialized Translator.

        Returns:
            A Translator.

        Raises:
            TypeError: If the object at `path` is not a Translator.

        See Also:
            The :meth:`Translator.store` method.
        """
        import pickle  # noqa: S403

        path = str(Path(str(path)).expanduser())
        with open(path, "rb") as f:
            ans = pickle.load(f)  # noqa: S301

        if not isinstance(ans, Translator):  # pragma: no cover
            raise TypeError(f"Serialized object at at path='{path}' is a {type(ans)}, not {Translator.__qualname__}.")

        return ans

    def store(
        self,
        translatable: DefaultTranslatable = None,
        names: Names = None,
        ignore_names: Names = None,
        delete_fetcher: bool = True,
        path: PathLikeType = DEFAULT_STORAGE_PATH,
        serialize: bool = False,
    ) -> "Translator":
        """Retrieve and store translations in memory.

        Args:
            translatable: Data from which IDs to fetch will be extracted. None=fetch all IDs.
            names: Explicit names to translate. Will try to derive form `translatable` if not given. May also be a
                predicate which indicates (returns True for) derived names to keep.
            ignore_names: Names **not** to translate. Always precedence over `names`, both explicit and derived. May
                also be a predicate which indicates (returns True for) names to ignore.
            delete_fetcher: If True, invoke :meth:`.Fetcher.close` and delete the fetcher after retrieving data. The
                Translator will still function, but some methods may raise exceptions and new data cannot be retrieved.
            path: Location where the serialized Translator will be stored on disk. Ignored when ``serialize==False``.
            serialize: If True, serialize the Translator to `path` once data has been retrieved.

        Returns:
            Self, for chained assignment.

        Raises:
            ForbiddenOperationError: If the fetcher does not permit the FETCH_ALL operation (only when `translatable` is
                None).
            MappingError: If a `translatable` is given, but no names to translate could be extracted.

        Notes:
            The Translator is guaranteed to be serializable once offline. Fetchers often aren't as they require things
            like database connections to function. Serializability can be tested using the
            :meth:`rics.utility.misc.serializable` method.

        See Also:
            The :meth:`Translator.restore` method.
        """
        if translatable is None:
            source_translations: SourcePlaceholderTranslations = self._fetch(None)
            translation_map = self._to_translation_map(source_translations)
        else:
            maybe_none, _ = self._get_updated_tmap(translatable, names, ignore_names=ignore_names, force_fetch=True)
            if maybe_none is None:
                raise MappingError("No values in the translatable were mapped. Cannot store translations.")
            translation_map = maybe_none  # mypy, would be cleaner to just use translation map..
            if LOGGER.isEnabledFor(logging.DEBUG):
                not_fetched = sorted(set(self._fetcher.sources).difference(translation_map.sources))
                LOGGER.debug(f"Available sources {not_fetched} were not fetched.")

        if delete_fetcher:  # pragma: no cover
            self._fetcher.close()
            del self._fetcher

        self._cached_tmap = translation_map

        if serialize:
            import os
            import pickle  # noqa: S403

            path = Path(str(path)).expanduser()
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "wb") as f:
                pickle.dump(self, f)

            mb_size = os.path.getsize(path) / 1000000
            LOGGER.info(f"Stored {self} of size {mb_size:.3g} MB at path='{path}'.")
        return self

    def _get_updated_tmap(
        self,
        translatable: DefaultTranslatable,
        names: Names = None,
        ignore_names: Names = None,
        force_fetch: bool = False,
    ) -> Tuple[Optional[TranslationMap], List[NameType]]:
        """Get an updated translation map.  # noqa

        Setting ``force_fetch=True`` will ignore the cached translation if there is one.

        Steps:
            1. Resolve which data structure IO to use, fail if not found.
            2. Resolve name-to-source mappings. If none are found, return None.
            3. Create a new translation map, or update the cached one.

        See the :meth:`translate`-method for more detailed documentation.
        """
        translatable_io = resolve_io(translatable)  # Fail fast if untranslatable type

        name_to_source = self.map_to_sources(translatable, names, ignore_names)
        if name_to_source is None:
            # Nothing to translate.
            return None, []  # pragma: no cover

        translation_map = (
            self.fetch(translatable, name_to_source, translatable_io)
            if force_fetch or not self._cached_tmap
            else self._cached_tmap
        )

        n2s = name_to_source.flatten()
        translation_map.name_to_source = n2s  # Update
        return translation_map, list(n2s)

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

        if self._default_fmt and "id" in self._default_fmt.placeholders and "id" not in placeholders:
            # Ensure that default translations can always use the ID
            placeholders = placeholders + ("id",)
            required = required + ("id",)

        return (
            self._fetcher.fetch_all(placeholders, required)
            if ids_to_fetch is None
            else self._fetcher.fetch(ids_to_fetch, placeholders, required)
        )

    def _to_translation_map(self, source_translations: SourcePlaceholderTranslations) -> TranslationMap:
        return TranslationMap(
            source_translations,
            fmt=self._fmt,
            default=self._default,
            default_fmt=self._default_fmt,
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

    @classmethod
    def _extract_from_attribute(cls, translatable: DefaultTranslatable) -> List[NameType]:
        no_use_keys = False
        for attr_name in _NAME_ATTRIBUTES:
            if attr_name == "keys" and no_use_keys:
                continue  # Pandas Series have keys, but should not be used.

            if hasattr(translatable, attr_name):
                attr = getattr(translatable, attr_name)
                if attr is None:
                    no_use_keys = True
                else:
                    return cls._dont_ruin_string(attr() if callable(attr) else attr)

        raise AttributeError(
            "Must pass 'names' since type " f"'{type(translatable)}' has none of {_NAME_ATTRIBUTES} as and attribute."
        )

    @classmethod
    def _resolve_names_inner(
        cls, names: List[NameType], ignored_names: Union[NamesPredicate, Set[NameType]]
    ) -> List[NameType]:
        predicate = _IgnoredNamesPredicate(ignored_names).apply
        names_to_translate = list(filter(predicate, names))
        if not names_to_translate and names:
            warnings.warn(f"No names left to translate. Ignored names: {ignored_names}, explicit names: {names}.")
        return names_to_translate

    @classmethod
    def _dont_ruin_string(cls, arg: Optional[NameTypes]) -> List[NameType]:
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


def _handle_default(
    fmt: Format,
    default_fmt: Optional[FormatType],
    default_translations: Optional[Union[InheritedKeysDict, MakeDict]],
) -> Tuple[Optional[InheritedKeysDict], Optional[Format]]:  # pragma: no cover
    if default_fmt is None and default_translations is None:
        return None, None

    dt: Optional[InheritedKeysDict] = None

    if isinstance(default_translations, InheritedKeysDict):
        dt = default_translations
    elif isinstance(default_translations, dict):
        dt = InheritedKeysDict.make(default_translations)

    dfmt: Optional[Format]
    if default_fmt is None:
        dfmt = None
    elif isinstance(default_fmt, str):
        dfmt = Format(default_fmt)
    else:
        dfmt = default_fmt

    if dt is not None and dfmt is None:
        # Force a default format if default translations are given
        dfmt = fmt

    if dfmt is not None:
        dt = dt or InheritedKeysDict()

    if dfmt is not None:
        extra = set(dfmt.placeholders).difference(fmt.placeholders)
        extra.discard("id")
        if extra:
            raise ValueError(
                f"The given fallback translation format {repr(default_fmt)} uses placeholders "
                f"{sorted(extra)} which are not in the main format, which is not supported."
            )

    return dt, dfmt
