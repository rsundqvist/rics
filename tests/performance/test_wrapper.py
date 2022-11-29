import sys
from pathlib import Path

import pandas as pd
import pytest
from click.testing import CliRunner

from rics.performance import MultiCaseTimer, cli, run_multivariate_test


def unload_modules():
    for key in list(filter(lambda s: "cli_modules" in s or "test_data" in s or "candidates" in s, sys.modules)):
        del sys.modules[key]


@pytest.mark.filterwarnings("ignore:The test results may be unreliable:UserWarning")
def test_cli_create():
    unload_modules()

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli.main,
            ["--time-per-candidate=0.01", "--create", "--name=create-unit-test"],
            catch_exceptions=False,
        )
    assert result.exit_code == 0


def get_raw_timings(self, func, test_data, repeat, number):
    return [func.sleep_multiplier * test_data] * repeat


@pytest.mark.parametrize("with_all", (False, True))
def test_cli(monkeypatch, with_all):
    monkeypatch.setattr(MultiCaseTimer, "_get_raw_timings", get_raw_timings)
    unload_modules()

    if with_all:
        from tests.performance.cli_modules.with_all import candidates, test_data
    else:
        from tests.performance.cli_modules.without_all import candidates, test_data  # type: ignore

    runner = CliRunner()
    with runner.isolated_filesystem() as tmpdir:
        with open(candidates.__file__) as f:
            Path(tmpdir).joinpath("candidates.py").write_text(f.read())
        with open(test_data.__file__) as f:
            Path(tmpdir).joinpath("test_data.py").write_text(f.read())

        result = runner.invoke(
            cli.main,
            ["--time-per-candidate=0.1", "--name=unit-test"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert Path(tmpdir).joinpath("unit-test.png").is_file()
        csv = Path(tmpdir).joinpath("unit-test.csv")
        assert csv.is_file()
        verify_ans(pd.read_csv(csv))


def test_run_multivariate_test(monkeypatch):
    monkeypatch.setattr(MultiCaseTimer, "_get_raw_timings", get_raw_timings)
    unload_modules()

    from tests.performance.cli_modules.with_all import candidates, test_data

    ans = run_multivariate_test(
        candidate_method=candidates.ALL,
        test_data=test_data.ALL,
        time_per_candidate=0.1,
    )
    verify_ans(ans)


def verify_ans(ans):
    assert sorted(ans["Candidate"].unique()) == ["sleep", "sleep_x4"]
    assert sorted(ans["Test data"].unique()) == ["1 ms", "3 ms"]
    best = ans.groupby(["Candidate", "Test data"])["Time [ms]"].min()
    assert (best["sleep"] < best["sleep_x4"]).all()
