import sys

from rics.performance import MultiCaseTimer, run_multivariate_test


def unload_modules():
    for key in list(
        filter(
            lambda s: "cli_modules" in s or "test_data" in s or "candidates" in s,
            sys.modules,
        )
    ):
        del sys.modules[key]


def get_raw_timings(_self, func, test_data, repeat, _number, /):
    return [func.sleep_multiplier * test_data] * repeat


def test_run_multivariate_test(monkeypatch):
    monkeypatch.setattr(MultiCaseTimer, "_get_raw_timings", get_raw_timings)
    unload_modules()

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
