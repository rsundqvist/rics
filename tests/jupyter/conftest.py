from dataclasses import dataclass
from pathlib import Path

import pytest

from rics.jupyter import VenvHelper


@dataclass(frozen=True)
class DummyProject:
    expected_manager: str
    working_dir: Path

    def verify_system_paths(self) -> None:
        helper = VenvHelper()
        assert helper.exec_prefix.startswith(str(self.working_dir))
        assert helper.executable.startswith(str(self.working_dir))


@pytest.fixture
def dummy_project(request: pytest.FixtureRequest, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> DummyProject:
    manager = request.param

    monkeypatch.chdir(tmp_path)
    tmp_path.joinpath(f"{manager}.lock").write_text(_UV_LOCK)
    tmp_path.joinpath("pyproject.toml").write_text(_PYPROJECT)

    return DummyProject(manager, tmp_path)


_PYPROJECT = """
[project]
name = "dummy-project"
version = "0.1.0"
"""

_UV_LOCK = """
version = 1
revision = 2
requires-python = ">=3.11"

[[package]]
name = "dummy-project"
version = "0.1.0"
source = { virtual = "." }
"""
