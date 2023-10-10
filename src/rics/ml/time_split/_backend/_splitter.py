import logging
from dataclasses import asdict, dataclass
from typing import Optional, Tuple

from pandas import Timestamp

from rics.misc import format_kwargs
from rics.performance import format_seconds

from ..types import DatetimeIterable, DatetimeSplitBounds, DatetimeSplits, Flex, Schedule, Span
from ._limits import LimitsTuple
from ._schedule import NO_LIMITS, MaterializedSchedule, materialize_schedule
from ._span import OffsetCalculator, to_strict_span

LOGGER = logging.getLogger("rics.ml.time_split")


@dataclass(frozen=True)
class DatetimeIndexSplitter:
    """Backend interface for splitting user data."""

    schedule: Schedule
    before: Span
    after: Span
    n_splits: Optional[int]
    flex: Flex

    def get_splits(self, available: DatetimeIterable = None) -> DatetimeSplits:
        """Compute a split of given user data."""
        ms = self._materialize_schedule(available)
        self._log_expansion(ms.available_metadata.limits, expanded=ms.available_metadata.expanded_limits)
        return self._make_bounds_list(ms)

    def get_plot_data(self, available: DatetimeIterable) -> Tuple[DatetimeSplits, MaterializedSchedule]:
        """Returns additional data needed to visualize folds."""
        ms = self._materialize_schedule(available)
        splits = self._make_bounds_list(ms)
        return splits, ms

    def _materialize_schedule(self, available: DatetimeIterable = None) -> MaterializedSchedule:
        ms = materialize_schedule(self.schedule, self.flex, available=available)
        if not ms.schedule.sort_values().equals(ms.schedule):
            raise ValueError(f"schedule must be sorted in ascending order; schedule={self.schedule!r} is not valid.")
        return ms

    def _make_bounds_list(self, ms: MaterializedSchedule) -> DatetimeSplits:
        get_start = OffsetCalculator(self.before, ms.schedule, ms.available_metadata.expanded_limits, name="before")
        get_end = OffsetCalculator(self.after, ms.schedule, ms.available_metadata.expanded_limits, name="after")

        min_start, max_end = ms.available_metadata.expanded_limits

        retval = []
        for i, mid in enumerate(ms.schedule):
            start, end = get_start(i), get_end(i)
            if start is None or start < min_start or start >= mid:
                continue
            if end is None or end > max_end or end <= mid:
                continue
            retval.append(DatetimeSplitBounds(start, mid, end))

        if not retval:
            # TODO Rapportera även expanded
            limits = ms.available_metadata.limits
            limits_info = "" if limits == NO_LIMITS else f"limits={tuple(map(str, limits))} and "
            raise ValueError(f"No valid splits with {limits_info}split params: ({format_kwargs(asdict(self))})")

        if self.n_splits:
            retval = retval[-self.n_splits :]

        return retval

    def _log_expansion(self, original: LimitsTuple, *, expanded: LimitsTuple) -> None:
        if original == expanded:
            return

        if not LOGGER.isEnabledFor(logging.INFO):
            return

        def stringify(old: Timestamp, *, new: Timestamp) -> str:
            from .._frontend._to_string import _PrettyTimestamp

            retval = f"{old} -> "
            if old == new:
                return retval + "<no change>"
            diff = (new - old).total_seconds()
            return retval + f"{_PrettyTimestamp(new).auto} ({'+' if diff > 0 else '-'}{format_seconds(abs(diff))})"

        LOGGER.info(
            f"Available data limits have been expanded (since flex={self.flex!r}):\n"
            f"  start: {stringify(original[0], new=expanded[0])}\n"
            f"    end: {stringify(original[1], new=expanded[1])}"
        )

    def __post_init__(self) -> None:
        # Verify n_splits
        if self.n_splits is not None and self.n_splits < 1:
            raise ValueError(f"Expected n_splits >= 1, but got n_splits={self.n_splits!r}.")

        # Verify before/after
        to_strict_span(self.before, name="before")
        to_strict_span(self.after, name="after")
