import pandas as pd
import pytest
from pandas import Timestamp
from rics.ml.time_split.settings import auto_flex as settings
from rics.ml.time_split.support import expand_limits


def _run(expected, flex, limits):
    actual = expand_limits(limits, flex=flex)
    assert actual == tuple(Timestamp(s) for s in expected.split(","))


@pytest.mark.parametrize(
    "actual, expected",
    [
        # Daily
        ("2019-05-10 22:35", "2019-05-11"),
        ("2019-05-10 18:35", "2019-05-10 18:35"),
        # Hourly
        ("2019-05-01 23:50", "2019-05-02"),
        ("2019-05-01 23:40", "2019-05-01 23:40"),
    ],
)
def test_auto(actual, expected):
    limits = Timestamp("2019-05"), Timestamp(actual)
    expected = f"2019-05, {expected}"

    _run(expected, "auto", limits)

    auto_equivalence = [settings.hour, settings.day]
    _run(expected, auto_equivalence, limits)
    _run(expected, reversed(auto_equivalence), limits)


@pytest.mark.parametrize(
    "flex, expected",
    [
        ("d", "2019-05-11, 2019-05-12"),
        ("h", "2019-05-11, 2019-05-11 23"),
    ],
)
def test_basic(flex, expected):
    limits = Timestamp("2019-05-11 00:15"), Timestamp("2019-05-11 22:35")
    _run(expected, flex, limits)


@pytest.mark.parametrize(
    "flex, expected",
    [
        ("d<1h", "2019-05-11, 2019-05-12"),
        ("d < 10 minutes", "2019-05-11 00:15, 2019-05-11 23:35"),
    ],
)
def test_tolerance(flex, expected):
    limits = Timestamp("2019-05-11 00:15"), Timestamp("2019-05-11 23:35")
    _run(expected, flex, limits)


@pytest.mark.parametrize(
    "enabled, expected",
    [
        (True, "2019-05-11 11:35"),
        (False, "2019-05-12"),
    ],
)
def test_sanity(enabled, expected, monkeypatch):
    monkeypatch.setattr(settings, "SANITY_CHECK", enabled)

    limits = Timestamp("2019-05-11"), Timestamp("2019-05-11 11:35")
    _run(f"2019-05-11,{expected}", "d", limits)


class TestErrors:
    limits = pd.Timestamp("1991-06-05"), pd.Timestamp("1999-04-30")

    @pytest.mark.parametrize(
        "start, stop",
        [
            ("2023-05-01", "2023-05-01"),
            ("2023-05-01 01", "2023-05-01"),
        ],
    )
    def test_bad_limits(self, start, stop):
        limits = pd.Timestamp(start), pd.Timestamp(stop)
        flex = ("this", "shouldn't", "matter")
        with pytest.raises(ValueError):
            expand_limits(limits, flex=flex)

    @pytest.mark.parametrize("round_to", ["1d", "2d", "-d"])
    def test_invalid_round_to_frequency(self, round_to):
        with pytest.raises(ValueError, match="not a valid frequency"):
            expand_limits(self.limits, flex=("2d", round_to, "3h"))

    @pytest.mark.parametrize(
        "start_at, tolerance",
        [
            ("-1d", "3d"),
            ("1d", "-1d"),
        ],
    )
    def test_negative(self, start_at, tolerance):
        with pytest.raises(ValueError, match="non-negative"):
            expand_limits(self.limits, flex=(start_at, "d", tolerance))

    @pytest.mark.parametrize(
        "order, start_at, round_to, tolerance",
        [
            ("start_at,round_to", "1h", "d", "2d"),
            ("round_to,tolerance", "1d", "d", "2d"),
        ],
    )
    def test_bad_inequality(self, start_at, round_to, tolerance, order):
        left, right = order.split(",")
        with pytest.raises(ValueError, match=f"{left}=.* < {right}="):
            expand_limits(self.limits, flex=(start_at, round_to, tolerance))

    def test_bad_level(self):
        with pytest.raises(AttributeError, match="Bad level='unknown'"):
            settings.set_level("unknown", start_at="", round_to="", tolerance="")  # type: ignore[arg-type]

    def test_bad_hour_setting(self, monkeypatch):
        monkeypatch.setattr(settings, "hour", ("2 days", "day", "15 min"))
        with pytest.raises(ValueError, match="Invalid settings: auto_flex.hour="):
            expand_limits(self.limits, flex=True)

    def test_bad_day_setting(self, monkeypatch):
        monkeypatch.setattr(settings, "day", ("2 hour", "hour", "1 hour"))
        with pytest.raises(ValueError, match="Invalid settings: auto_flex.day="):
            expand_limits(self.limits, flex=True)
