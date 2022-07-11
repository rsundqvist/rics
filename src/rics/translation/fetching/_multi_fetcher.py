import logging
import warnings
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from time import perf_counter
from typing import Any, Callable, Dict, Iterable, List, Tuple

from rics.performance import format_perf_counter
from rics.translation.fetching import Fetcher, exceptions
from rics.translation.fetching.types import IdsToFetch
from rics.translation.offline.types import SourcePlaceholderTranslations
from rics.translation.types import IdType, SourceType
from rics.utility.action_level import ActionLevel, ActionLevelHelper
from rics.utility.collections.dicts import compute_if_absent, reverse_dict
from rics.utility.misc import tname

LOGGER = logging.getLogger(__package__).getChild("MultiFetcher")

FetchResult = Tuple[int, SourcePlaceholderTranslations]

_ACTION_LEVEL_HELPER = ActionLevelHelper(
    duplicate_translation_action=ActionLevel.IGNORE,
    duplicate_source_discovered_action=None,
)


def _invoke(func: Callable, *args: Any) -> FetchResult:
    return id(func.__self__), func(*args)  # type: ignore


class MultiFetcher(Fetcher[SourceType, IdType]):
    """Fetcher which combines the results of other fetchers."""

    def __init__(
        self,
        *fetchers: Fetcher,
        max_workers: int = 2,
        duplicate_translation_action: ActionLevel = ActionLevel.WARN,
        duplicate_source_discovered_action: ActionLevel = ActionLevel.IGNORE,
    ) -> None:
        for pos, f in enumerate(fetchers):  # pragma: no cover
            if not isinstance(f, Fetcher):
                raise TypeError(f"Argument {pos} is of type {type(f)}, expected Fetcher subtype.")

        self._id_to_rank: Dict[int, int] = {id(f): rank for rank, f in enumerate(fetchers)}
        self._id_to_fetcher: Dict[int, Fetcher] = {id(f): f for f in fetchers}
        self._source_to_fetcher_id_actual: Dict[SourceType, int] = {}
        self.max_workers: int = max_workers
        self._duplicate_translation_action = _ACTION_LEVEL_HELPER.verify(
            duplicate_translation_action, "duplicate_translation_action"
        )
        self._duplicate_source_discovered_action = _ACTION_LEVEL_HELPER.verify(
            duplicate_source_discovered_action, "duplicate_source_discovered_action"
        )

        if len(self) != len(fetchers):  # pragma: no cover
            raise ValueError("Repeat fetcher instance(s)!")

    @property
    def allow_fetch_all(self) -> bool:
        return all(f.allow_fetch_all for f in self._id_to_fetcher.values())  # pragma: no cover

    def online(self) -> bool:
        return all(f.online for f in self._id_to_fetcher.values())  # pragma: no cover

    @property
    def placeholders(self) -> Dict[SourceType, List[str]]:
        return {
            source: self._id_to_fetcher[self._source_to_fetcher_id[source]].placeholders[source]
            for source in self.sources
        }

    @property
    def fetchers(self) -> List[Fetcher[SourceType, IdType]]:
        """Return child fetchers."""
        return list(self._id_to_fetcher.values())

    @property
    def sources(self) -> List[SourceType]:
        return list(self._source_to_fetcher_id)

    def fetch(
        self,
        ids_to_fetch: Iterable[IdsToFetch[SourceType, IdType]],
        placeholders: Iterable[str] = (),
        required: Iterable[str] = (),
    ) -> SourcePlaceholderTranslations[SourceType]:
        tasks: Dict[int, List[IdsToFetch]] = {fid: [] for fid in self._id_to_fetcher}
        num_instructions = 0
        for idt in ids_to_fetch:
            fetcher_id = self._source_to_fetcher_id[idt.source]
            tasks[fetcher_id].append(idt)
            num_instructions += 1

        placeholders = tuple(placeholders)
        required = tuple(required)

        start = perf_counter()
        LOGGER.debug(
            f"Dispatch {num_instructions} jobs to {len(self)} " f"different fetchers using {self.max_workers} threads."
        )

        with ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix=tname(self)) as executor:
            futures = [
                executor.submit(_invoke, self._id_to_fetcher[fid].fetch, task_list, placeholders, required)
                for fid, task_list in tasks.items()
            ]
            ans = self._gather(futures)
            LOGGER.debug(f"All jobs completed in {format_perf_counter(start)}.")
            return ans

    def fetch_all(
        self, placeholders: Iterable[str] = (), required: Iterable[str] = ()
    ) -> SourcePlaceholderTranslations:
        placeholders = tuple(placeholders)
        required = tuple(required)

        start = perf_counter()
        LOGGER.debug(f"Dispatch FETCH_ALL jobs to {len(self)} " f"different fetchers using {self.max_workers} threads.")
        with ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix=tname(self)) as executor:
            futures = [
                executor.submit(_invoke, fetcher.fetch_all, placeholders, required)
                for fetcher in self._id_to_fetcher.values()
            ]
            ans = self._gather(futures)
            LOGGER.debug(f"All FETCH_ALL jobs completed in {format_perf_counter(start)}.")
            return ans

    @property
    def duplicate_translation_action(self) -> ActionLevel:
        """Return action to take when multiple fetchers return translations for the same source."""
        return self._duplicate_translation_action

    @property
    def duplicate_source_discovered_action(self) -> ActionLevel:
        """Return action to take when multiple fetchers claim the same source."""
        return self._duplicate_source_discovered_action

    @property
    def _source_to_fetcher_id(self) -> Dict[SourceType, int]:
        if not self._source_to_fetcher_id_actual:
            source_ranks: Dict[SourceType, int] = {}
            source_to_fetcher_id: Dict[SourceType, int] = {}

            for fid, fetcher in self._id_to_fetcher.items():
                rank = self._id_to_rank[fid]
                for source in fetcher.sources:
                    if source in source_to_fetcher_id:
                        self._log_rejection(source, rank, source_ranks[source], translation=False)
                    else:
                        source_to_fetcher_id[source] = fid
                        source_ranks[source] = rank
            self._source_to_fetcher_id_actual = source_to_fetcher_id

        return self._source_to_fetcher_id_actual

    def _gather(self, futures: Iterable[Future]) -> SourcePlaceholderTranslations[SourceType]:
        ans: SourcePlaceholderTranslations = {}
        source_ranks: Dict[SourceType, int] = {}

        for future in as_completed(futures):
            fid, translations = future.result()
            rank = self._id_to_rank[fid]
            self._process_future_result(translations, rank, source_ranks, ans)
        return ans

    def _process_future_result(
        self,
        translations: SourcePlaceholderTranslations[SourceType],
        rank: int,
        source_ranks: Dict[SourceType, int],
        ans: SourcePlaceholderTranslations[SourceType],
    ) -> None:
        for source_translations in translations.values():
            source = source_translations.source
            other_rank = compute_if_absent(source_ranks, source, lambda _: rank)

            if other_rank != rank:
                self._log_rejection(source, rank, other_rank, translation=True)
                if rank > other_rank:
                    continue  # Don't save -- other rank is greater (lower-is-better).

            ans[source] = source_translations

    def _log_rejection(self, source: SourceType, rank0: int, rank1: int, translation: bool) -> None:  # pragma: no cover
        accepted_rank, rejected_rank = (rank0, rank1) if rank0 < rank1 else (rank1, rank0)

        rank_to_id = reverse_dict(self._id_to_rank)
        fmt = "rank-{} fetcher {}@{}"
        accepted_fetcher = self._id_to_fetcher[rank_to_id[accepted_rank]]
        accepted = fmt.format(accepted_rank, accepted_fetcher, hex(id(accepted_fetcher)))
        rejected_fetcher = self._id_to_fetcher[rank_to_id[rejected_rank]]
        rejected = fmt.format(rejected_rank, rejected_fetcher, hex(id(rejected_fetcher)))

        msg = (
            f"Discarded translations for {source=} retrieved from {rejected} since the {accepted} returned "
            "translations for the same source."
            if translation
            else f"Discarded {source=} retrieved from {rejected} since the {accepted} already claimed same source."
        )

        msg += " Hint: Rank is determined input order at initialization."

        action = self.duplicate_translation_action if translation else self.duplicate_source_discovered_action

        if action is ActionLevel.IGNORE:
            LOGGER.debug(msg)
        else:
            if action is ActionLevel.RAISE:
                LOGGER.error(msg)
                raise exceptions.DuplicateSourceError(msg)
            else:
                warnings.warn(msg, exceptions.DuplicateSourceWarning)
                LOGGER.warning(msg)

    def __len__(self) -> int:
        return len(self._id_to_fetcher)

    def __repr__(self) -> str:
        fetchers = list(self._id_to_fetcher.values())
        max_workers = self.max_workers
        duplicate_translation_action = self.duplicate_translation_action
        return f"{tname(self)}({fetchers=}, {max_workers=}, {duplicate_translation_action=})"
