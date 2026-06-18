import io
import logging

from rics.performance._progress import _LoggingProgress, _NullProgress, _TqdmProgress, make_progress

LOGGER = logging.getLogger("test.performance.progress")


class _Tty(io.StringIO):
    def isatty(self) -> bool:
        return True


class _NotTty(io.StringIO):
    def isatty(self) -> bool:
        return False


def test_disabled_returns_null():
    assert isinstance(make_progress(3, enabled=False, logger=LOGGER), _NullProgress)


def test_non_tty_uses_logging():
    progress = make_progress(3, enabled=True, logger=LOGGER, stream=_NotTty())
    assert isinstance(progress, _LoggingProgress)


def test_tty_uses_tqdm():
    progress = make_progress(3, enabled=True, logger=LOGGER, stream=_Tty())
    # tqdm is a test/dev dependency; if missing we fall back to logging, which is also acceptable.
    assert isinstance(progress, (_TqdmProgress, _LoggingProgress))
    progress.close()


def test_logging_progress_emits_final_line(caplog):
    progress = _LoggingProgress(2, LOGGER, min_interval=1e9)  # huge interval -> only the final (100%) line logs
    progress.set_description("candidate(x)")
    with caplog.at_level(logging.INFO, logger=LOGGER.name):
        progress.update()
        progress.update()
    messages = [r.getMessage() for r in caplog.records]
    assert messages == ["Progress: 2/2 (100%) candidate(x)"]
