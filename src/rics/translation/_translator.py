import logging
import warnings
from collections import defaultdict
from pathlib import Path
from time import perf_counter
from typing import Any, Dict, Generic, Iterable, List, Optional, Set, Tuple, Type, Union

from rics._internal_support.types import PathLikeType
from rics.mapping import DirectionalMapping, Mapper
from rics.mapping.exceptions import MappingError, MappingWarning, UserMappingError
from rics.performance import format_perf_counter
from rics.translation import factory
from rics.translation.dio import DataStructureIO, resolve_io
from rics.translation.exceptions import ConnectionStatusError, TooManyFailedTranslationsError
from rics.translation.fetching import Fetcher
from rics.translation.fetching.exceptions import UnknownSourceError
from rics.translation.fetching.types import IdsToFetch
from rics.translation.offline import Format, TranslationMap
from rics.translation.offline.types import FormatType, PlaceholderTranslations, SourcePlaceholderTranslations
from rics.translation.types import (
    ID,
    ExtendedOverrideFunction,
    IdType,
    Names,
    NamesPredicate,
    NameType,
    NameTypes,
    SourceType,
    Translatable,
)
from rics.utility.collections.dicts import InheritedKeysDict, MakeType
from rics.utility.misc import tname

_NAME_ATTRIBUTES = ("name", "names", "columns", "keys")

LOGGER = logging.getLogger(__package__).getChild("Translator")

FetcherTypes = Union[
    Fetcher[SourceType, IdType],
    TranslationMap[NameType, SourceType, IdType],
    SourcePlaceholderTranslations[SourceType],
    Dict[SourceType, PlaceholderTranslations.MakeTypes],
]


class Translator(Generic[Translatable, NameType, SourceType, IdType]):
    """Translate IDs to human-readable labels.

    The recommended way of initializing ``Translator`` instances is the :meth:`from_config` method. For configuration
    file details, please refer to the :ref:`translator-config` page.

    The `Translator` is the main entry point for all translation tasks. Simplified translation process steps:

        1. The :attr:`map_to_sources` method performs name-to-source mapping (see :class:`.DirectionalMapping`).
        2. The :attr:`fetch` method extracts IDs to translate and retrieves data (see :class:`.TranslationMap`).
        3. Finally, the :attr:`translate` method applies the translations and returns to the caller.

    Args:
        fetcher: A :class:`.Fetcher` or ready-to-use translations.
        fmt: String :class:`.Format` specification for translations.
        mapper: A :class:`.Mapper` instance for binding names to sources.
        default_fmt: Alternative :class:`.Format` to use instead of `fmt` for fallback translation of unknown IDs.
        default_fmt_placeholders: Shared and/or source-specific default placeholder values for unknown IDs. See
            :meth:`.InheritedKeysDict.make` for details.

    Notes:
        Untranslatable IDs will be ``None`` by default if neither `default_fmt` nor `default_fmt_placeholders` is given.
        Adding the `maximal_untranslated_fraction` option to :meth:`translate` will raise an exceptions if too many IDs
        are left untranslated. Note however that this verifiction step may be expensive.

    Examples:
        A minimal example. For a more complete use case, see the :ref:`dvdrental` example. Assume that we have data for
        people and animals as in the table below::

            people:                       animals:
                 id | name    | gender       id | name   | is_nice
              ------+---------+--------     ----+--------+---------
               1991 | Richard | Male          0 | Tarzan | false
               1999 | Sofia   | Female        1 | Morris | true
               1904 | Fred    | Male          2 | Simba  | true

        In most real cases we'd fetch this table from somewhere. In this case, howeever, there's so little data that we
        can simply enumerate the components needed for translation ourselves to create a :class:`.MemoryFetcher`.

        >>> from rics.translation import Translator
        >>> translation_data = {
        ...     'animals': {'id': [0, 1, 2], 'name': ['Tarzan', 'Morris', 'Simba'], 'is_nice': [False, True, True]},
        ...     'people': {'id': [1999, 1991, 1904], 'name': ['Sofia', 'Richard', 'Fred']},
        ... }
        >>> translator = Translator(translation_data, fmt='{id}:{name}[, nice={is_nice}]')
        >>> data = {'animals': [0, 2], 'people': [1991, 1999]}
        >>> for key, translated_table in translator.translate(data).items():
        >>>     print(f'Translations for {repr(key)}:')
        >>>     for translated_id in translated_table:
        >>>         print(f'    {repr(translated_id)}')
        Translations for 'animals':
            '0:Tarzan, nice=False'
            '2:Simba, nice=True'
        Translations for 'people':
            '1991:Richard'
            '1999:Sofia'

        Handling unknown IDs.

        >>> default_fmt_placeholders = dict(
        ...     default={'is_nice': 'Maybe?', 'name': "Bob"},
        ...     specific={'animals': {'name': 'Fido'}},
        >>> )
        >>> useless_database = {
        ...     'animals': {'id': [], 'name': []},
        ...     'people': {'id': [], 'name': []}
        >>> }
        >>> translator = Translator(useless_database, default_fmt_placeholders=default_fmt_placeholders,
        ...                         fmt='{id}:{name}[, nice={is_nice}]')
        >>> data = {'animals': [0], 'people': [0]}
        >>> for key, translated_table in translator.translate(data).items():
        >>>     print(f'Translations for {repr(key)}:')
        >>>     for translated_id in translated_table:
        >>>         print(f'    {repr(translated_id)}')
        Translations for 'animals':
            '0:Fido, nice=Maybe?'
        Translations for 'people':
            '0:Bob, nice=Maybe?'

        Since we didn't give an explicit `default_fmt_placeholders`, the regular `fmt` is used instead. Formats can be
        plain strings, in which case tranlation will never explicitly fail unless the name itself fails to map and
        :attr:`.Mapper.unmapped_values_action` is set to :attr:`.ActionLevel.RAISE`.
    """

    def __init__(
        self,
        fetcher: FetcherTypes,
        fmt: FormatType = "{id}:{name}",
        mapper: Mapper[NameType, SourceType, None] = None,
        default_fmt: FormatType = None,
        default_fmt_placeholders: MakeType = None,
    ) -> None:
        self._fmt = fmt if isinstance(fmt, Format) else Format(fmt)
        self._mapper = mapper or Mapper()
        self._default_fmt_placeholders, self._default_fmt = _handle_default(
            self._fmt, default_fmt, default_fmt_placeholders
        )

        self._cached_tmap: TranslationMap
        if isinstance(fetcher, Fetcher):
            self._fetcher: Fetcher = fetcher
            self._cached_tmap = TranslationMap({})
        elif isinstance(fetcher, dict):
            self._cached_tmap = self._to_translation_map(
                {source: PlaceholderTranslations.make(source, pht) for source, pht in fetcher.items()}
            )
        elif isinstance(fetcher, TranslationMap):
            tmap = fetcher.copy()
            tmap.fmt = self._fmt
            tmap.default_fmt = self._default_fmt
            tmap.default_fmt_placeholders = self._default_fmt_placeholders  # type: ignore
            self._cached_tmap = tmap
        else:
            raise TypeError(type(fetcher))  # pragma: no cover

    @classmethod
    def from_config(
        cls,
        path: PathLikeType,
        extra_fetchers: Iterable[str] = (),
    ) -> "Translator":
        """Create a ``Translator`` from TOML inputs.

        Args:
            path: Path to a TOML file, or a pre-parsed dict.
            extra_fetchers: Path to TOML files defining additional fetchers. Useful for fetching from multiple sources
                or kinds of sources, for example locally stored files in conjunction with one or more databases. The
                fetchers are ranked by input order, with the fetcher defined in `path` being given the highest priority
                (rank 0).

        Returns:
            A ``Translator`` instance.

        See Also:
            The :ref:`translator-config` page.
        """
        return factory.TranslatorFactory(path, extra_fetchers).create()

    def copy(self, share_fetcher: bool = True, **overrides: Any) -> "Translator":
        """Make a copy of this ``Translator``.

        Args:
            share_fetcher: If ``True``, the returned instance use the same ``Fetcher``.
            overrides: Keyword arguments to use when instantiating the copy. Options that aren't given will be taken
                from the current instance. See the :class:`Translator` class documentation for possible choices.

        Returns:
            A copy of this ``Translator`` with `overrides` applied.

        Raises:
            NotImplementedError: If ``share_fetcher=False``.
        """
        if not share_fetcher:
            raise NotImplementedError("Fetcher cloning not implemented.")

        kwargs: Dict[str, Any] = {
            "fmt": self._fmt,
            "default_fmt": self._default_fmt,
            **overrides,
        }

        if "mapper" not in kwargs:  # pragma: no cover
            kwargs["mapper"] = self.mapper.copy()

        if "default_fmt_placeholders" not in kwargs:
            kwargs["default_fmt_placeholders"] = self._default_fmt_placeholders

        if "fetcher" not in kwargs:
            kwargs["fetcher"] = self.fetcher if self.online else self._cached_tmap.copy()

        return Translator(**kwargs)

    def translate(
        self,
        translatable: Translatable,
        names: Names = None,
        ignore_names: Names = None,
        inplace: bool = False,
        override_function: ExtendedOverrideFunction = None,
        maximal_untranslated_fraction: float = 1.0,
        reverse: bool = False,
    ) -> Optional[Translatable]:
        """Translate IDs to human-readable strings.

        Args:
            translatable: A data structure to translate.
            names: Explicit names to translate. Will try to derive form `translatable` if not given. May also be a
                predicate which indicates (returns ``True`` for) derived names to keep.
            ignore_names: Names **not** to translate. Always precedence over `names`, both explicit and derived. May
                also be a predicate which indicates (returns ``True`` for) names to ignore.
            inplace: If ``True``, translation is performed in-place and this function returns ``None``.
            override_function: A callable with inputs (value, candidates, ids) that returns either ``None``, the source
                to use, or a split mapping ``{source: [ids_for_source..]}`` which forces IDs to be fetched from
                different sources in spite of being labelled with the same name.
            maximal_untranslated_fraction: The maximum fraction of IDs for which translation may fail before an error is
                raised. 1=disabled. Ignored in `reverse` mode.
            reverse: If ``True``, perform reverse translations back to IDs instead. Offline mode only.

        Returns:
            A copy of `translatable` with IDs replaced by translations if ``inplace=False``, otherwise ``None``.

        Raises:
            UntranslatableTypeError: If `translatable` is not translatable using any standard IOs.
            AttributeError: If `names` are not given and cannot be derived from `translatable`.
            MappingError: If required (explicitly given) names fail to map to a source.
            ValueError: If `maximal_untranslated_fraction` is not a valid fraction.
            TooManyFailedTranslationsError: If translation fails for more than `maximal_untranslated_fraction` of IDs.
            ConnectionStatusError: If ``reverse=True`` while the ``Translator`` is online.
            UnknownSourceError: If `override_function` returns a source which is not known to the ``Translator``.

        See Also:
            The :meth:`.Mapper.apply` function, which performs both placeholder and name-to-source mapping.
        """
        if self.online and reverse:  # pragma: no cover
            raise ConnectionStatusError("Reverse translation cannot be performed online.")

        if not (0.0 <= maximal_untranslated_fraction <= 1):  # pragma: no cover
            raise ValueError(f"Argument {maximal_untranslated_fraction=} is not a valid fraction")

        translation_map, names_to_translate = self._get_updated_tmap(
            translatable,
            names,
            ignore_names=ignore_names,
            override_function=override_function,
        )
        if not translation_map:
            return None if inplace else translatable  # pragma: no cover

        translatable_io = resolve_io(translatable)
        if LOGGER.isEnabledFor(logging.DEBUG) or maximal_untranslated_fraction < 1:
            self._verify_translations(
                translatable, names_to_translate, translation_map, translatable_io, maximal_untranslated_fraction
            )

        if reverse:
            translation_map.reverse_mode = True
            try:
                return translatable_io.insert(
                    translatable, names=names_to_translate, tmap=translation_map, copy=not inplace
                )
            finally:
                translation_map.reverse_mode = False

        else:
            return translatable_io.insert(
                translatable, names=names_to_translate, tmap=translation_map, copy=not inplace
            )

    def __call__(
        self,
        translatable: Translatable,
        names: Names = None,
        ignore_names: Names = None,
        inplace: bool = False,
    ) -> Optional[Translatable]:
        """Inherits docstring from self.translate."""
        return self.translate(translatable, names, ignore_names, inplace)  # pragma: no cover

    __call__.__doc__ = translate.__doc__

    def map_to_sources(
        self,
        translatable: Translatable,
        names: Names = None,
        ignore_names: Names = None,
        override_function: ExtendedOverrideFunction = None,
    ) -> Optional[DirectionalMapping]:
        """Map names to translation sources.

        Args:
            translatable: A data structure to map names for.
            names: Explicit names to translate. Will try to derive form `translatable` if not given. May also be a
                predicate which indicates (returns ``True`` for) derived names to keep.
            ignore_names: Names **not** to translate. Always precedence over `names`, both explicit and derived. May
                also be a predicate which indicates (returns ``True`` for) names to ignore.
            override_function: A callable with inputs ``(value, candidates, ids)`` that returns either ``None``, the
                ``source`` to use, or a split mapping ``{source: [ids_for_source..]}`` which forces IDs to be fetched
                from different sources.

        Returns:
            A mapping of names to translation sources. Returns ``None`` if mapping failed.

        Raises:
            AttributeError: If `names` are not given and cannot be derived from `translatable`.
            MappingError: If required (explicitly given) names fail to map to a source.
            UnknownSourceError: If `override_function` returns a source which is not known to the ``Translator``.
        """
        names_to_translate = self._resolve_names(translatable, names, ignore_names)
        sources = self.fetcher.sources if self.online else self._cached_tmap.sources

        def func(value: NameType, candidates: Set[SourceType], _: None) -> Optional[SourceType]:
            assert override_function is not None, "This shouldn't happen"  # noqa: S101
            res = override_function(value, candidates, [])
            if res is None:
                return None
            if isinstance(res, dict):
                raise NotImplementedError(
                    "Name splitting is not yet supported. See https://github.com/rsundqvist/rics/issues/64"
                )
            else:
                return res

        if override_function is None:
            name_to_source = self.mapper(names_to_translate, sources)
        else:
            try:
                name_to_source = self.mapper(names_to_translate, sources, override_function=func)
            except UserMappingError as e:
                raise UnknownSourceError(e.value, e.candidates) from e

        # Fail if any of the explicitly given (ie literal, not predicate) names fail to map to a source.
        if isinstance(names, (str, Iterable)):
            required = set(self._dont_ruin_string(names))
            unmapped = required.difference(name_to_source.left)
            if unmapped:
                raise MappingError(f"Required names {unmapped} not mapped with {sources=} and {ignore_names=}.")

        if not name_to_source.left:
            msg = f"Translation aborted since none of {names=} could be mapped with {sources=}"
            warnings.warn(msg, MappingWarning)
            LOGGER.warning(msg)
            return None

        return name_to_source

    def fetch(
        self,
        translatable: Translatable,
        name_to_source: DirectionalMapping[NameType, SourceType],
        data_structure_io: Type[DataStructureIO] = None,
    ) -> TranslationMap:
        """Fetch translations.

        Args:
            translatable: A data structure to translate.
            name_to_source: Mappings of names in `translatable` to :attr:`~.Fetcher.sources` as they are known to the
                :attr:`fetcher`.
            data_structure_io: Data Structure IO class used to extract IDs from `translatable`. Derive if ``None``.

        Returns:
            A :class:`.TranslationMap`.

        Raises:
            ConnectionStatusError: If disconnected from the fetcher, ie not :attr:`online`.
        """
        ids_to_fetch = self._get_ids_to_fetch(
            name_to_source, translatable, data_structure_io or resolve_io(translatable)
        )
        source_translations = self._fetch(ids_to_fetch)
        return self._to_translation_map(source_translations)

    @property
    def online(self) -> bool:
        """Return connectivity status. If ``False``, no new translations may be fetched."""
        return hasattr(self, "_fetcher")

    @property
    def fetcher(self) -> Fetcher[SourceType, IdType]:
        """Return the ``Fetcher`` instance used to retrieve translations."""
        if not self.online:
            raise ConnectionStatusError("Cannot fetch new translations.")  # pragma: no cover

        return self._fetcher

    @property
    def mapper(self) -> Mapper[NameType, SourceType, None]:
        """Return the ``Mapper`` instance used for name-to-source binding."""
        return self._mapper

    @property
    def cache(self) -> TranslationMap[NameType, SourceType, IdType]:
        """Return a ``TranslationMap`` of cached translations."""
        return self._cached_tmap

    @classmethod
    def restore(cls, path: PathLikeType) -> "Translator":
        """Restore a serialized ``Translator``.

        Args:
            path: Path to a serialized ``Translator``.

        Returns:
            A ``Translator``.

        Raises:
            TypeError: If the object at `path` is not a ``Translator``.

        See Also:
            The :meth:`Translator.store` method.
        """
        import pickle  # noqa: S403

        path = str(Path(str(path)).expanduser())
        with open(path, "rb") as f:
            ans = pickle.load(f)  # noqa: S301

        if not isinstance(ans, Translator):  # pragma: no cover
            raise TypeError(f"Serialized object at at {path=} is a {type(ans)}, not {Translator.__name__}.")

        return ans

    def store(
        self,
        translatable: Translatable = None,
        names: Names = None,
        ignore_names: Names = None,
        delete_fetcher: bool = True,
        path: PathLikeType = None,
    ) -> "Translator":
        """Retrieve and store translations in memory.

        Args:
            translatable: Data from which IDs to fetch will be extracted. Fetch all IDs if ``None``.
            names: Explicit names to translate. Will try to derive form `translatable` if not given. May also be a
                predicate which indicates (returns ``True`` for) derived names to keep.
            ignore_names: Names _not_ to translate. Always takes precedence over `names`, both explicit and derived. May
                also be a predicate which indicates names to ignore.
            delete_fetcher: If ``True``, invoke :meth:`.Fetcher.close` and delete the fetcher after retrieving data. The
                ``Translator`` will still function, but new data cannot be retrieved.
            path: If given, serialize the ``Translator`` to disk after retrieving data.

        Returns:
            Self, for chained assignment.

        Raises:
            ForbiddenOperationError: If the fetcher does not permit the FETCH_ALL operation (only when `translatable` is
                ``None``).
            MappingError: If a `translatable` is given, but no names to translate could be extracted.

        Notes:
            The ``Translator`` is guaranteed to be serializable once offline. Fetchers often aren't as they require
            things like database connections to function. Serializability can be tested using the
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
                not_fetched = set(self.fetcher.sources).difference(translation_map.sources)
                LOGGER.debug(f"Available sources {not_fetched} were not fetched.")

        if delete_fetcher:  # pragma: no cover
            self.fetcher.close()
            del self._fetcher

        self._cached_tmap = translation_map

        if path:
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
        translatable: Translatable,
        names: Names = None,
        ignore_names: Names = None,
        override_function: ExtendedOverrideFunction = None,
        force_fetch: bool = False,
    ) -> Tuple[Optional[TranslationMap], List[NameType]]:
        """Get an updated translation map.  # noqa

        Setting ``force_fetch=True`` will ignore the cached translation if there is one.

        Steps:
            1. Resolve which data structure IO to use, fail if not found.
            2. Resolve name-to-source mappings. If none are found, return ``None``.
            3. Create a new translation map, or update the cached one.

        See the :meth:`translate`-method for more detailed documentation.
        """
        translatable_io = resolve_io(translatable)  # Fail fast if untranslatable type

        name_to_source = self.map_to_sources(translatable, names, ignore_names, override_function)
        if name_to_source is None:
            # Nothing to translate.
            return None, []  # pragma: no cover

        translation_map = (
            self.fetch(translatable, name_to_source, translatable_io) if force_fetch or not self.cache else self.cache
        )

        n2s = name_to_source.flatten()
        translation_map.name_to_source = n2s  # Update
        return translation_map, list(n2s)

    @staticmethod
    def _get_ids_to_fetch(
        name_to_source: DirectionalMapping,
        translatable: Translatable,
        dio: Type[DataStructureIO],
    ) -> List[IdsToFetch]:

        # Aggregate and remove duplicates.
        source_to_ids: Dict[SourceType, Set[IdType]] = defaultdict(set)
        for name, ids in dio.extract(translatable, list(name_to_source.left)).items():
            source_to_ids[name_to_source.left_to_right[name][0]].update(ids)  # type: ignore

        return [IdsToFetch(source, ids) for source, ids in source_to_ids.items()]

    def _fetch(self, ids_to_fetch: Optional[List[IdsToFetch]]) -> SourcePlaceholderTranslations:
        fetcher = self.fetcher

        placeholders = self._fmt.placeholders
        required = self._fmt.required_placeholders

        if self._default_fmt and ID in self._default_fmt.placeholders and ID not in placeholders:
            # Ensure that default translations can always use the ID
            placeholders = placeholders + (ID,)
            required = required + (ID,)

        return (
            fetcher.fetch_all(placeholders, required)
            if ids_to_fetch is None
            else fetcher.fetch(ids_to_fetch, placeholders, required)
        )

    def _to_translation_map(self, source_translations: SourcePlaceholderTranslations) -> TranslationMap:
        return TranslationMap(
            source_translations,
            fmt=self._fmt,
            default_fmt=self._default_fmt,
            default_fmt_placeholders=self._default_fmt_placeholders,
        )

    @staticmethod
    def _verify_translations(
        translatable: Translatable,
        names_to_translate: List[NameType],
        translation_map: TranslationMap,
        translatable_io: Type[DataStructureIO],
        maximal_untranslated_fraction: float,
    ) -> None:
        start = perf_counter()
        copied_map = translation_map.copy()
        # TODO: Remove the ignores when https://github.com/python/mypy/issues/3004 (5+ years old..) is fixed.
        copied_map.fmt = "found"  # type: ignore
        copied_map.default_fmt = ""  # type: ignore
        ans = translatable_io.insert(translatable, names=names_to_translate, tmap=copied_map, copy=True)
        extracted = translatable_io.extract(ans, names=names_to_translate)

        for name, translations in extracted.items():
            fraction = sum(t == "" for t in translations) / len(translations)

            source = translation_map.name_to_source[name]
            msg = f"Failed to translate {fraction:.3%} of IDs for {name=} using {source=}."
            if LOGGER.isEnabledFor(logging.DEBUG):
                LOGGER.debug(msg)
            if fraction > maximal_untranslated_fraction:
                raise TooManyFailedTranslationsError(
                    msg + f" Limit: maximal_untranslated_fraction={maximal_untranslated_fraction:.3%}"
                )

        n_ids = sum(map(len, extracted.values()))
        LOGGER.debug(f"Verified {n_ids} IDs from {len(extracted)} different sources in {format_perf_counter(start)}.")

    def __repr__(self) -> str:
        more = f"fetcher={self.fetcher}" if self.online else f"cache={self.cache}"

        online = self.online
        return f"{tname(self)}({online=}: {more})"

    def _resolve_names(
        self,
        translatable: Translatable,
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
    def _extract_from_attribute(cls, translatable: Translatable) -> List[NameType]:
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
    default_fmt_placeholders: Optional[MakeType],
) -> Tuple[Optional[InheritedKeysDict], Optional[Format]]:  # pragma: no cover
    if default_fmt is None and default_fmt_placeholders is None:
        return None, None

    dt: Optional[InheritedKeysDict] = None

    if isinstance(default_fmt_placeholders, InheritedKeysDict):
        dt = default_fmt_placeholders
    elif isinstance(default_fmt_placeholders, dict):
        dt = InheritedKeysDict.make(default_fmt_placeholders)

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

    return dt, dfmt
