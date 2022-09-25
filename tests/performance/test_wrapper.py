from dataclasses import dataclass
from time import sleep

import pytest

from rics.performance import MultiCaseTimer, run_multivariate_test


@dataclass(frozen=True)
class CandidateFunction:
    sleep_multiplier: int

    def __call__(self, time):
        sleep(time * self.sleep_multiplier)


def get_raw_timings(self, func, test_data, repeat, number):
    return [func.sleep_multiplier * test_data] * repeat


MultiCaseTimer._get_raw_timings = get_raw_timings  # type: ignore


@pytest.mark.filterwarnings("ignore:Matplotlib is currently using agg:UserWarning")
def test_run_multivariate_test():
    ans = run_multivariate_test(
        candidate_method={
            "sleep": CandidateFunction(1),
            "sleep_x4": CandidateFunction(4),
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
