import pytest

from rics.strings import format_bytes


@pytest.mark.parametrize(
    "n, binary, expected",
    [
        (1024**8, True, "1.00 YiB"),
        (1024**9, True, "1024.00 YiB"),
        (1000**10, False, "1.00 QB"),
        (1000**11, False, "1000.00 QB"),
    ],
)
def test_beyond_largest_prefix(n, binary, expected):
    assert format_bytes(n, binary=binary) == expected
