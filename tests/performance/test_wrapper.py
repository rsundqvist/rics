from time import sleep

import pytest

from rics.performance import run_multivariate_test


@pytest.mark.filterwarnings("ignore:Matplotlib is currently using agg:UserWarning")
@pytest.mark.filterwarnings("ignore:The test results may be unreliable:UserWarning")
def test_run_multivariate_test():
    ans = run_multivariate_test(
        candidate_method={
            "sleep": lambda t: sleep(t),
            "sleep_x4": lambda t: sleep(t * 4),
        },
        test_data={
            "1 ms": 0.001,
            "3 ms": 0.003,
        },
        time_per_candidate=0.1,
    )
    assert sorted(ans["Candidate"].unique()) == ["sleep", "sleep_x4"]
    assert sorted(ans["Test data"].unique()) == ["1 ms", "3 ms"]

    best = ans.groupby(["Candidate", "Test data"])["Time [ms]"].min()
    assert (best["sleep"] < best["sleep_x4"]).all()
