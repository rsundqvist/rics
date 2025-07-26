import json
import logging

import pytest
from click.testing import CliRunner

from rics import __version__ as expected_version
from rics import cli
from rics.jupyter import KernelHelper
from rics.jupyter._venv_helper import Resolve


@pytest.mark.parametrize("dummy_project", ["uv", "poetry"], indirect=True)
def test_jupyter(dummy_project, monkeypatch):
    real = KernelHelper._check_call

    def check_call(_, args, timeout):
        assert args[1:] == [
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--quiet",
            "--require-virtualenv",
            "ipykernel",
        ]
        assert timeout >= 180
        real(args, timeout)

    monkeypatch.setattr("rics.logs.LoggingSetupHelper._on_verbosity_zero", lambda _: None)
    monkeypatch.setattr("rics.jupyter._kernel_helper.KernelHelper._check_call", check_call)

    result = CliRunner().invoke(
        cli.main,
        ["k", "-p0", "-e", "TEST_ENV_KEY", "TEST_ENV_VALUE", "--prefix", dummy_project.working_dir],
        env={"JUPYTER_PLATFORM_DIRS": "1", "POETRY_VIRTUALENVS_IN_PROJECT": "1"},
    )
    assert result.exit_code == 0

    lines = result.stdout.splitlines()
    assert len(lines) == 2

    helper = KernelHelper()

    # Verify target
    expected_path = dummy_project.working_dir / "share/jupyter/kernels" / helper.resolve_kernel_name()
    assert str(expected_path) in lines[-1]

    # Verify KernelSpec JSON.
    kernel_spec = KernelHelper.read_kernel_spec(expected_path / "kernel.json")

    # Top level - these are read by e.g. Jupyter Lab.
    assert kernel_spec["env"]["TEST_ENV_KEY"] == "TEST_ENV_VALUE"
    assert kernel_spec["display_name"] == helper.resolve_display_name()

    # Internal metadata. Useful for debugging but not much else.
    metadata = kernel_spec["metadata"]["rics.jupyter"]

    venv = metadata["venv"]
    assert venv["manager"] == dummy_project.expected_manager
    assert venv["slug"] == helper.venv.slug
    assert "dummy-project" in helper.venv.slug

    installer = metadata["installer"]
    assert installer["version"] == expected_version

    dummy_project.verify_project()


@pytest.mark.parametrize("drop", ["argv", "display_name", "language"])
def test_corrupt_kernel_spec(tmp_path, drop):
    kernel_spec = {
        "argv": ["/usr/bin/python", "-m", "ipykernel_launcher", "-f", "{connection_file}"],
        "display_name": "rics-py3.11 [poetry]",
        "env": {"PYDEVD_DISABLE_FILE_VALIDATION": "1"},
        "language": "python",
        "metadata": {
            "debugger": True,
            "rics.jupyter": {
                "installer": {"version": "5.0.1.dev1"},
                "venv": {"manager": "poetry", "slug": "rics-py3.11"},
            },
        },
    }

    del kernel_spec[drop]

    path = tmp_path / "kernel.json"
    path.write_text(json.dumps(kernel_spec))

    with pytest.raises(TypeError, match=repr(drop)):
        KernelHelper.read_kernel_spec(path)


def test_uv_bad_pyproject(tmp_path, monkeypatch, caplog):
    monkeypatch.chdir(tmp_path)
    tmp_path.joinpath("pyproject.toml").write_text("[uv]\n# Bad project file!")

    actual = Resolve.uv(tmp_path, logging.getLogger(test_uv_bad_pyproject.__name__))
    assert actual is None
    assert "No `project` table found" in caplog.text
