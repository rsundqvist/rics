from time import sleep

from rics.performance import run_multivariate_test


def test_run_multivariate_test():
    ans = run_multivariate_test(
        candidate_method={
            "sleep": lambda t: sleep(t),
            "sleep_x5": lambda t: sleep(t * 5),
        },
        test_data={
            "50 ms": 0.050,
            "75 ms": 0.075,
        },
        time_per_candidate=0.5,
    )
    assert sorted(ans["Candidate"].unique()) == ["sleep", "sleep_x5"]
    assert sorted(ans["Test data"].unique()) == ["50 ms", "75 ms"]

    best = ans.groupby(["Candidate", "Test data"])["Time [ms]"].min()
    assert all(best["sleep"] * 3 < best["sleep_x5"]) and all(best["sleep_x5"] < best["sleep"] * 6)
