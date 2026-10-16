"""Pytest fixtures, loaded through ``pytest_plugins``.

Imports ``pytest`` at module scope since fixtures need the decorator; never import this module from ``rics`` itself.
"""

import logging
import sys
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from types import ModuleType


@pytest.fixture
def tmp_path_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Run the test with `tmp_path` as the working directory."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def restore_logging() -> Iterator[None]:
    """Restore the level, handlers, ``propagate`` and ``disabled`` of every logger after the test.

    Loggers created during the test are reset to the state of a new logger. Handlers are re-attached as-is; one that
    the test closed (e.g. through ``logging.basicConfig(force=True)``) stays closed.
    """

    def loggers() -> Iterator[logging.Logger]:
        yield logging.root
        yield from (lg for lg in logging.Logger.manager.loggerDict.values() if isinstance(lg, logging.Logger))

    snapshot = {lg: (lg.level, lg.propagate, lg.disabled, list(lg.handlers)) for lg in loggers()}
    disable = logging.root.manager.disable

    yield

    logging.disable(disable)
    for lg in loggers():
        level, lg.propagate, lg.disabled, lg.handlers[:] = snapshot.get(lg, (logging.NOTSET, True, False, []))
        lg.setLevel(level)  # Clears the isEnabledFor-cache, unlike assigning `level` directly.


@pytest.fixture
def unload_modules() -> Iterator[Callable[..., None]]:
    """Unload modules so that the test imports them anew; restore the original ``sys.modules`` entries afterwards.

    Call the returned function with module names; each name covers its submodules as well. Modules first imported
    during the test are unloaded again at teardown.
    """
    names: list[str] = []
    snapshot: dict[str, ModuleType] = {}

    def matching() -> list[str]:
        return [m for m in sys.modules if any(m == name or m.startswith(f"{name}.") for name in names)]

    def unload(*modules: str) -> None:
        names.extend(modules)
        for m in matching():
            snapshot.setdefault(m, sys.modules.pop(m))

    yield unload

    for m in matching():
        del sys.modules[m]
    sys.modules.update(snapshot)
