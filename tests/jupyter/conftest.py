import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

from rics.jupyter import VenvHelper
from rics.jupyter._venv_helper import _make_breakout_env


@dataclass(frozen=True)
class DummyProject:
    expected_manager: str
    working_dir: Path

    def verify_project(self) -> None:
        helper = VenvHelper()
        assert helper.exec_prefix.startswith(str(self.working_dir))
        assert helper.executable.startswith(str(self.working_dir))

        self._assert_packages_are_installed(helper.executable)

    @classmethod
    def _assert_packages_are_installed(cls, python: str) -> None:
        subprocess.check_call([python, "-c", "import pytest"])
        subprocess.check_call([python, "-c", "import ipykernel"])


@pytest.fixture
def dummy_project(request: pytest.FixtureRequest, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> DummyProject:
    manager = request.param

    monkeypatch.chdir(tmp_path)
    tmp_path.joinpath("pyproject.toml").write_text(_PYPROJECT)
    # tmp_path.joinpath("src/").write_text()

    # Break out of the caller's environment so `uv`/`poetry` operate on the dummy project's own venv; otherwise the
    # nox-injected UV_PROJECT_ENVIRONMENT/UV_PYTHON would make `uv sync` prune the nox venv instead.
    env = _make_breakout_env()
    env["POETRY_VIRTUALENVS_IN_PROJECT"] = "1"

    subprocess.check_output([manager, "lock"], env=env)
    assert tmp_path.joinpath(f"{manager}.lock").is_file()
    subprocess.check_output([manager, "sync"], env=env)

    return DummyProject(manager, tmp_path)


_PYPROJECT = f"""# See {__file__}
[project]
name = "dummy-project"
version = "0.1.0"

requires-python = ">=3.11"

dependencies = [
    "pytest == {pytest.__version__}",
]

[tool.poetry]
package-mode = false
"""
