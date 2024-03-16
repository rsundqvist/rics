import logging
from collections.abc import Callable, Iterable, MutableMapping, Sequence
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Union

from rics.misc import get_by_full_name

from ..settings import log_split_progress as settings
from ..types import DatetimeSplitBounds
from ._to_string import _PrettyTimestamp

LoggerArg = Union[logging.Logger, logging.LoggerAdapter, str]  # type: ignore[type-arg]


def log_split_progress(
    splits: Sequence[DatetimeSplitBounds],
    *,
    logger: LoggerArg = "rics.ml.time_split",
    start_level: int = logging.INFO,
    end_level: int = logging.INFO,
    extra: dict[str, Any] | None = None,
) -> Iterable[DatetimeSplitBounds]:
    """Log iteration progress over `splits` using `logger`.

    Args:
        splits: Splits to iterate over.
        logger: Logger or logger name to use.
        start_level: Log level to use for the :attr:`fold-begin message <.settings.log_split_progress.START_MESSAGE>`.
        end_level: Log level to use for the :attr:`fold-end message <.settings.log_split_progress.END_MESSAGE>`.
        extra: User-defined `extra`-arguments to use when logging, merged with progress-related extras. Will be
            available to all messages as well as the ``fold`` key. This argument is mutable; changes made to `extra`
            will be reflected in logged records.

    Returns:
        An iterable over `splits`.

    Examples:
        Basic usage.

        >>> from rics.ml.time_split import split, log_split_progress
        >>> splits = split("36h", available=("2023-08-10", "2023-08-19"))
        >>> tracked_splits = log_split_progress(
        ...     splits, logger="progress", start_level=logging.DEBUG
        ... )
        >>> list(tracked_splits)  # doctest: +SKIP
        [progress:DEBUG] Begin fold 1/2: ('2023-08-11' <= [schedule: '2023-08-16' (Wednesday)] < '2023-08-17 12:00:00').
        [progress:INFO] Finished fold 1/2 [schedule: '2023-08-16' (Wednesday)] after 5m 18s.
        [progress:DEBUG] Begin fold 2/2: ('2023-08-12 12:00:00' <= [schedule: '2023-08-17 12:00:00' (Thursday)] < '2023-08-19').
        [progress:INFO] Finished fold 2/2 [schedule: '2023-08-17 12:00:00' (Thursday)] after 4m 3s.
    """
    logger = logging.getLogger(logger) if isinstance(logger, str) else logger

    if isinstance(logger, logging.LoggerAdapter) and not hasattr(logger, "merge_extra"):
        # Backport of https://github.com/python/cpython/pull/107292
        logger = _MergingLoggerAdapter(logger.logger, logger.extra)

    track = _ProgressTracker(
        logger=logger,
        fold_format=settings.FOLD_FORMAT,
        start_level=start_level,
        start_message=settings.START_MESSAGE,
        end_level=end_level,
        end_message=settings.END_MESSAGE,
        seconds_formatter=settings.SECONDS_FORMATTER
        if callable(settings.SECONDS_FORMATTER)
        else get_by_full_name(settings.SECONDS_FORMATTER),
        user_extra=extra or {},
    )
    return track(splits)


@dataclass(frozen=True)
class _ProgressTracker:
    logger: logging.Logger | logging.LoggerAdapter  # type: ignore[type-arg]
    fold_format: str
    start_level: int
    start_message: str
    end_level: int
    end_message: str
    seconds_formatter: Callable[[float], str]
    user_extra: dict[str, Any]

    def __call__(self, splits: Sequence[DatetimeSplitBounds]) -> Iterable[DatetimeSplitBounds]:
        n_splits = len(splits)

        for n, split in enumerate(splits, start=1):
            extra: dict[str, str | float | int | bool] = dict(
                n=n,
                n_splits=n_splits,
                start=split.start.isoformat(),
                mid=split.mid.isoformat(),
                end=split.end.isoformat(),
                **self.user_extra,
            )
            kwargs: dict[str, Any] = dict(
                n=n,
                n_splits=n_splits,
                start=_PrettyTimestamp(split.start),
                mid=_PrettyTimestamp(split.mid),
                end=_PrettyTimestamp(split.end),
                **self.user_extra,
            )
            kwargs.update(fold=self.fold_format.format(**kwargs))

            self.logger.log(self.start_level, self.start_message.format(**kwargs), extra=extra)

            # Yield split and count user time.
            start = perf_counter()
            yield split
            seconds = round(perf_counter() - start, 6)

            kwargs.update(
                seconds=seconds,
                formatted_seconds=self.seconds_formatter(seconds),
            )
            extra.update(seconds=seconds)
            self.logger.log(self.end_level, self.end_message.format(**kwargs), extra=extra)


class _MergingLoggerAdapter(logging.LoggerAdapter):  # type: ignore[type-arg]
    def process(self, msg: Any, kwargs: MutableMapping[str, Any]) -> tuple[Any, MutableMapping[str, Any]]:
        """See https://github.com/python/cpython/pull/107292."""
        kwargs["extra"] = {**self.extra, **kwargs["extra"]} if "extra" in kwargs and self.extra else self.extra
        return msg, kwargs
