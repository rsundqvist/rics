import os
import time

DATE_COLUMNS = ["rental_date", "return_date"]

DOCKER_COMMAND = (
    "docker run -p 5001:5432 moertel/postgresql-sample-dvdrental"
    "@sha256:e35f8dc4011d053777631208c85e3976a422b65e12383579d8a856a7849082c5"
)


def wait_for_dvdrental(sleep: float = 0.5, attempts: int = 3) -> bool:
    if "CI" in os.environ:
        # https://docs.github.com/en/actions/learn-github-actions/environment-variables
        return False

    for _ in range(attempts):
        ready = os.system("/usr/bin/pg_isready -h localhost -p 5001 -U postgres -d dvdrental")  # noqa: S605
        if ready == 0:  # Ready
            return True
        time.sleep(sleep)
    return False
