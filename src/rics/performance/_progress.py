"""Progress reporting for :class:`.MultiCaseTimer` runs.

Uses ``tqdm`` for interactive (TTY) output, and falls back to periodic ``logging`` when output is not a terminal -- so
captured/CI logs get readable progress lines instead of carriage-return spam (and ``tqdm`` becomes optional).
"""

import logging
import sys
import time
from typing import Any, Protocol, TextIO


class Progress(Protocol):
    """Minimal progress-reporter interface."""

    def set_description(self, desc: str) -> None:
        """Set the text shown alongside progress."""

    def update(self, n: int = 1) -> None:
        """Advance progress by `n` steps."""

    def close(self) -> None:
        """Finalize the reporter."""


class _NullProgress:
    def set_description(self, desc: str) -> None: ...
    def update(self, n: int = 1) -> None: ...
    def close(self) -> None: ...


class _TqdmProgress:
    def __init__(self, total: int) -> None:
        from tqdm.auto import tqdm

        self._bar = tqdm(total=total)

    def set_description(self, desc: str) -> None:
        self._bar.set_description_str(desc, refresh=True)

    def update(self, n: int = 1) -> None:
        self._bar.update(n)

    def close(self) -> None:
        self._bar.close()


class _LoggingProgress:
    """Logs progress at most once per `min_interval` seconds (plus a final 100% line)."""

    def __init__(
        self,
        total: int,
        logger: logging.Logger | logging.LoggerAdapter[Any],
        *,
        min_interval: float = 1.0,
    ) -> None:
        self._total = total
        self._logger = logger
        self._min_interval = min_interval
        self._n = 0
        self._desc = ""
        self._last = time.perf_counter()

    def set_description(self, desc: str) -> None:
        self._desc = desc

    def update(self, n: int = 1) -> None:
        self._n += n
        now = time.perf_counter()
        if self._n >= self._total or (now - self._last) >= self._min_interval:
            self._last = now
            pct = 100 * self._n / self._total if self._total else 100.0
            suffix = f" {self._desc}" if self._desc else ""
            self._logger.info("Progress: %d/%d (%.0f%%)%s", self._n, self._total, pct, suffix)

    def close(self) -> None: ...


def make_progress(
    total: int,
    *,
    enabled: bool,
    logger: logging.Logger | logging.LoggerAdapter[Any],
    stream: TextIO | None = None,
) -> Progress:
    """Create a :class:`Progress` reporter.

    Returns a no-op reporter when ``enabled=False``, a ``tqdm`` bar when `stream` is a TTY (and ``tqdm`` is installed),
    and a logging-based reporter otherwise.
    """
    if not enabled:
        return _NullProgress()

    stream = stream if stream is not None else sys.stderr
    if getattr(stream, "isatty", lambda: False)():
        try:
            return _TqdmProgress(total)
        except ImportError:
            logger.debug("tqdm not installed; falling back to logging-based progress.")

    return _LoggingProgress(total, logger)
