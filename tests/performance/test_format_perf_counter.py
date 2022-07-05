import pytest as pytest

from rics.performance import format_perf_counter


@pytest.mark.parametrize(
    "end, expected",
    [
        (0.00000001, "1e-08 sec"),
        (0.0000002, "2e-07 sec"),
        (0.000003, "3e-06 sec"),
        (0.00004, "4e-05 sec"),
        (0.0001, "0.0001 sec"),
        (0.001, "0.001 sec"),
        (0.753, "0.753 sec"),
        (1.0, "1.00 sec"),
        (1.5, "1.50 sec"),
        (21780, "6:03:00"),
        (21780.49, "6:03:00"),
        (21780.51, "6:03:01"),
    ],
)
def test_format_perf_counter(end, expected):
    assert format_perf_counter(0, end) == expected
