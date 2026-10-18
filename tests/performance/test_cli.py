from pathlib import Path

import pandas as pd
import pytest
from click.testing import CliRunner

from rics import cli
from rics.performance import MultiCaseTimer
from rics.performance import cli as performance_cli

from .test_wrapper import CLI_MODULES, get_raw_timings, verify


@pytest.mark.filterwarnings("ignore:Results may be unreliable:UserWarning")
@pytest.mark.usefixtures("tmp_path_cwd")
def test_cli_create(unload_modules):
    unload_modules(*CLI_MODULES)

    result = CliRunner().invoke(
        cli.main,
        ["-v", "timeit", "--time-per-candidate=0.01", "--create", "--name=create-unit-test"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stderr


@pytest.mark.filterwarnings("ignore:Results may be unreliable:UserWarning")
@pytest.mark.usefixtures("tmp_path_cwd", "restore_logging")
def test_cli_standalone(unload_modules):
    """Invoked without the `rics` group, as by the `mtimeit` entrypoint; configures logging itself."""
    unload_modules(*CLI_MODULES)

    result = CliRunner().invoke(
        performance_cli.main,
        ["--time-per-candidate=0.01", "--create", "--name=standalone-unit-test"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stderr


@pytest.mark.usefixtures("tmp_path_cwd", "restore_logging")  # No -v: disables logging.root.
def test_cli_no_case_data(unload_modules):
    unload_modules(*CLI_MODULES)
    Path("candidates.py").write_text("def candidate_noop(data):\n    pass\n")
    Path("test_data.py").write_text("not_a_case = 1\n")

    result = CliRunner().invoke(cli.main, ["timeit"])

    assert result.exit_code != 0
    assert "ABORT: No case data given." in result.output
    assert "'test_data.py'" in result.output


@pytest.mark.parametrize("plot", (False, True))
@pytest.mark.parametrize("with_all", (False, True))
def test_cli(monkeypatch, tmp_path_cwd, unload_modules, with_all, plot):
    monkeypatch.setattr(MultiCaseTimer, "_get_raw_timings", get_raw_timings)
    unload_modules(*CLI_MODULES)

    if with_all:
        from tests.performance.cli_modules.with_all import candidates, test_data
    else:
        from tests.performance.cli_modules.without_all import (  # type: ignore
            candidates,
            test_data,
        )

    tmp_path_cwd.joinpath("candidates.py").write_text(Path(candidates.__file__).read_text())
    tmp_path_cwd.joinpath("test_data.py").write_text(Path(test_data.__file__).read_text())

    result = CliRunner().invoke(
        cli.main,
        ["-v", "timeit", "--time-per-candidate=0.1", "--name=unit-test", "--plot" if plot else "--no-plot"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert tmp_path_cwd.joinpath("unit-test.jpg").is_file() == plot
    csv = tmp_path_cwd.joinpath("unit-test.csv")
    assert csv.is_file()
    verify(pd.read_csv(csv))
