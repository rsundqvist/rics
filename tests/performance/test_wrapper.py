from rics.performance import MultiCaseTimer, run_multivariate_test

# The CLI imports `candidates` and `test_data` from the working directory.
CLI_MODULES = ("candidates", "test_data", "tests.performance.cli_modules")


def get_raw_timings(_self, func, test_data, repeat, _number, /, **_):
    return [func.sleep_multiplier * test_data] * repeat


def test_run_multivariate_test(monkeypatch, unload_modules):
    monkeypatch.setattr(MultiCaseTimer, "_get_raw_timings", get_raw_timings)
    unload_modules(*CLI_MODULES)

    from tests.performance.cli_modules.with_all import candidates, test_data

    result = run_multivariate_test(
        candidate_method=candidates.ALL,
        test_data=test_data.ALL,
        time_per_candidate=0.1,
    )
    verify(result)


def verify(result):
    assert sorted(result["Candidate"].unique()) == ["sleep", "sleep_x4"]
    assert sorted(result["Test data"].unique()) == ["1 ms", "3 ms"]
    best = result.groupby(["Candidate", "Test data"])["Time [ms]"].min()
    assert (best["sleep"] < best["sleep_x4"]).all()
