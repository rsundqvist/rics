from time import sleep

import pytest

from rics.performance import run_multivariate_test


@pytest.mark.filterwarnings("ignore:Matplotlib is currently using agg:UserWarning")
@pytest.mark.filterwarnings("ignore:The test results may be unreliable:UserWarning")
def test_run_multivariate_test():
    ans = run_multivariate_test(
        candidate_method={
            "sleep": lambda t: sleep(t),
            "sleep_x5": lambda t: sleep(t * 5),
        },
        test_data={
            "5 ms": 0.0050,
            "7.5 ms": 0.0075,
        },
        time_per_candidate=0.1,
    )
    assert sorted(ans["Candidate"].unique()) == ["sleep", "sleep_x5"]
    assert sorted(ans["Test data"].unique()) == ["5 ms", "7.5 ms"]

    best = ans.groupby(["Candidate", "Test data"])["Time [ms]"].min()
    assert (best["sleep"] < best["sleep_x5"]).all()
