import pytest as pytest

from rics.performance import format_perf_counter, format_seconds


class Base:
    @staticmethod
    def test_positive(t, expected):
        assert format_seconds(t) == expected
        assert format_perf_counter(0, t) == expected

    @staticmethod
    def test_negative(t, expected):
        t = -t
        expected = f"-{expected}"

        with pytest.raises(ValueError):
            format_seconds(t)
        assert format_seconds(t, allow_negative=True) == expected


@pytest.mark.parametrize(
    "t, expected",
    [
        (0.0000000000021, "2.1e-12s"),
        (0.0000000011, "1ns"),
        (0.00000002, "20ns"),
        (0.0000002, "200ns"),
        (0.0000051, "5μs"),
        (0.00002, "20μs"),
        (0.0002, "200μs"),
        (0.0011, "1ms"),
        (0.02, "20ms"),
        (0.20, "200ms"),
        (0.50, "500ms"),
    ],
)
class TestSubSecond(Base):
    pass


@pytest.mark.parametrize(
    "t, expected",
    [
        (0.51, "0.51s"),
        (0.515, "0.52s"),
        (0.81, "0.81s"),
        (1.00, "1.0s"),
        (1.01, "1.0s"),
        (1.251, "1.3s"),
    ],
)
class TestSecond(Base):
    pass


@pytest.mark.parametrize(
    "t, expected",
    [
        (123.3, "2m 3s"),
        (18003.9, "5h 0m 4s"),
        (18363.9, "5h 6m 4s"),
        (7794363.9, "90d 5h 6m 4s"),
    ],
)
class TestClock(Base):
    pass


@pytest.mark.parametrize(
    "t, expected",
    [
        (119.5, "2m"),
        (119.49, "1m 59s"),
        (3599.5, "1h"),
        (3599.49, "59m 59s"),
        (3659.5, "1h 1m"),
        (3659.49, "1h 0m 59s"),
    ],
)
class TestBoundaryClock(Base):
    pass
