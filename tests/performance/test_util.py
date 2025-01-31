import pytest

from rics.performance import format_perf_counter, format_seconds


class TestDeprecated:
    def format_perf_counter(self):
        with pytest.warns(DeprecationWarning, match="format_perf_counter"):
            actual = format_perf_counter(0, 7794363.9)
        assert actual == "90d 5h 6m 4s"

    def test_seconds(self):
        with pytest.warns(DeprecationWarning, match="format_seconds"):
            actual = format_seconds(7794363.9)
        assert actual == "90d 5h 6m 4s"
