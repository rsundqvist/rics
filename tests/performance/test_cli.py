from pathlib import Path

import pandas as pd
import pytest
from click.testing import CliRunner

from rics import cli
from rics.performance import MultiCaseTimer

from .test_wrapper import get_raw_timings, unload_modules, verify


@pytest.mark.filterwarnings("ignore:The test results may be unreliable:UserWarning")
def test_cli_create():
    unload_modules()

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli.main,
            ["-v", "timeit", "--time-per-candidate=0.01", "--create", "--name=create-unit-test"],
            catch_exceptions=False,
        )
    assert result.exit_code == 0, result.stderr


@pytest.mark.parametrize("with_all", (False, True))
def test_cli(monkeypatch, with_all):
    monkeypatch.setattr(MultiCaseTimer, "_get_raw_timings", get_raw_timings)
    unload_modules()

    if with_all:
        from tests.performance.cli_modules.with_all import candidates, test_data
    else:
        from tests.performance.cli_modules.without_all import (  # type: ignore
            candidates,
            test_data,
        )

    runner = CliRunner()
    with runner.isolated_filesystem() as tmp:
        with Path(candidates.__file__).open() as f:
            Path(tmp).joinpath("candidates.py").write_text(f.read())
        with Path(test_data.__file__).open() as f:
            Path(tmp).joinpath("test_data.py").write_text(f.read())

        result = runner.invoke(
            cli.main,
            ["-v", "timeit", "--time-per-candidate=0.1", "--name=unit-test"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert Path(tmp).joinpath("unit-test.jpg").is_file()
        csv = Path(tmp).joinpath("unit-test.csv")
        assert csv.is_file()
        verify(pd.read_csv(csv))
