from typing import Any, Callable

from tests.performance.cli_modules.without_all import candidates as _private

ALL: dict[str, Callable[[Any], None]] = {
    "sleep": _private.candidate_sleep,
    "sleep_x4": _private.candidate_sleep_x4,
}
