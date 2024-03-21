from dataclasses import dataclass
from time import sleep as real_sleep


@dataclass(frozen=True)
class CandidateFunction:
    sleep_multiplier: int

    def __call__(self, time: float) -> None:
        real_sleep(time * self.sleep_multiplier)

    @property
    def __name__(self) -> str:
        return "sleep" if self.sleep_multiplier == 1 else f"sleep_x{self.sleep_multiplier}"


candidate_sleep = CandidateFunction(1)
candidate_sleep_x4 = CandidateFunction(4)
