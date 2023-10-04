import pytest

from rics.ml.time_split import split
from rics.ml.time_split._backend._span import InvalidSpanError

from .conftest import SPLIT_DATA


def test_no_splits():
    with pytest.raises(ValueError, match="No valid splits with"):
        split(schedule="1d", before="100000d", available=SPLIT_DATA)


def test_unbounded_schedule():
    with pytest.raises(ValueError, match="explicit when not bounded by an available range"):
        split("1d")


@pytest.mark.parametrize("available", ["2022, 2022", "2022"])
def test_bad_limits(available):
    with pytest.raises(ValueError, match="at least two unique elements"):
        split("1d", available=available.split(","))


@pytest.mark.parametrize("span", [-1, "-1d", -5, "-100m", 0, "0 minutes"])
def test_invalid_offset(span):
    with pytest.raises(InvalidSpanError, match="'before'.* greater than zero"):
        split("1d", before=span, available=SPLIT_DATA)

    with pytest.raises(InvalidSpanError, match="'after'.* greater than zero"):
        split("1d", after=span, available=SPLIT_DATA)


def test_all_without_available():
    schedule = ["1991", "1999", "2019"]
    with pytest.raises(InvalidSpanError, match="'before'.* requires available data"):
        split(schedule, before="all", available=None)
    with pytest.raises(InvalidSpanError, match="'after'.* requires available data"):
        split(schedule, after="all", available=None)


def test_negative_n_splits():
    with pytest.raises(ValueError):
        split("1d", n_splits=-1)


def test_negative_schedule():
    schedule = "-1d"
    with pytest.raises(ValueError, match=f"unbounded.* {schedule=} .* greater than zero"):
        split(schedule, available=SPLIT_DATA)


def test_schedule_not_sorted():
    schedule = ["1999", "2019", "1991"]
    with pytest.raises(ValueError, match="sorted") as e:
        split(schedule)
    assert f"{schedule=}" in str(e.value)  # List repr is valid regex; can't put it in match=... as-is
