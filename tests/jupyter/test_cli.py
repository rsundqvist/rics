import json

import pytest
from click.testing import CliRunner

from rics import __version__ as expected_version
from rics import cli
from rics.jupyter import KernelHelper


def test_jupyter(tmp_path, monkeypatch):
    called = 0

    def do_nothing(_):
        # Default is to set logging.root.disabled=True, breaking other tests.
        nonlocal called
        called += 1

    monkeypatch.setattr("rics.logs.LoggingSetupHelper._on_verbosity_zero", do_nothing)

    result = CliRunner().invoke(
        cli.main,
        ["kernel", "-e", "TEST_ENV_KEY", "TEST_ENV_VALUE", "--prefix", tmp_path],
        env={"JUPYTER_PLATFORM_DIRS": "1"},
    )
    assert result.exit_code == 0
    assert called == 1

    lines = result.stdout.splitlines()
    assert len(lines) == 2

    helper = KernelHelper()

    # Verify target
    expected_path = tmp_path / "share/jupyter/kernels" / helper.resolve_kernel_name()
    assert str(expected_path) in lines[-1]

    # Verify KernelSpec JSON.
    kernel_spec = KernelHelper.read_kernel_spec(expected_path / "kernel.json")

    # Top level - these are read by e.g. Jupyter Lab.
    assert kernel_spec["env"]["TEST_ENV_KEY"] == "TEST_ENV_VALUE"
    assert kernel_spec["display_name"] == helper.resolve_display_name()

    # Internal metadata. Useful for debugging but not much else.
    metadata = kernel_spec["metadata"]["rics.jupyter"]

    venv = metadata["venv"]
    assert venv["manager"] == "poetry"
    assert venv["slug"] == helper.venv.slug

    installer = metadata["installer"]
    assert installer["version"] == expected_version


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
