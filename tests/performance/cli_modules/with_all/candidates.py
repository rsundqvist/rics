from tests.performance.cli_modules.without_all import candidates as _private

ALL = {
    "sleep": _private.candidate_sleep,
    "sleep_x4": _private.candidate_sleep_x4,
}
