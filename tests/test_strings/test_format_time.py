import pytest

from rics.strings import format_perf_counter, format_seconds


class Base:
    full: bool

    @classmethod
    def test_positive(cls, t, expected):
        assert format_seconds(t, full=cls.full) == expected
        assert format_perf_counter(0, end=t, full=cls.full) == expected

    @classmethod
    def test_negative(cls, t, expected):
        t = -t
        expected = f"-{expected}"

        with pytest.raises(ValueError):
            format_seconds(t)
        assert format_seconds(t, allow_negative=True, full=cls.full) == expected


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
    full = True  # Doesn't matter


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
    full = True  # Doesn't matter


@pytest.mark.parametrize(
    "t, expected",
    [
        (123.3, "2m 3s"),
        (18003.9, "5h 0m 4s"),
        (18363.9, "5h 6m 4s"),
        (7794363.9, "90d 5h 6m 4s"),
    ],
)
class TestClockFull(Base):
    full = True


@pytest.mark.parametrize(
    "t, expected",
    [
        (123.3, "2m 3s"),
        (18003.9, "5h"),
        (18363.9, "5h 6m"),
        (7794363.9, "90d 5h 6m"),
    ],
)
class TestClock(Base):
    full = False


TRANSITION_CASES = [(59.99, "60.0s"), (60.00, "60.0s"), (60.01, "1m"), (61.0, "1m 1s")]


@pytest.mark.parametrize("t, expected", TRANSITION_CASES)
class TestClockTransitionFull(Base):
    full = True


@pytest.mark.parametrize("t, expected", TRANSITION_CASES)
class TestClockTransition(Base):
    full = False


@pytest.mark.parametrize(
    "t, expected",
    [
        (119.49, "1m 59s"),
        (119.50, "2m"),
        (119.51, "2m"),
        (3599.50, "1h"),
        (3599.49, "59m 59s"),
        (3659.50, "1h 1m"),
        (3659.49, "1h 0m 59s"),
    ],
)
class TestBoundaryClockFull(Base):
    full = True


@pytest.mark.parametrize(
    "t, expected",
    [
        (119.49, "1m 59s"),
        (119.50, "2m"),
        (119.51, "2m"),
        (3599.50, "1h"),
        (3599.49, "59m 59s"),
        (3659.50, "1h 1m"),
        (3659.49, "1h 0m 59s"),
    ],
)
class TestBoundaryClock(Base):
    full = False
