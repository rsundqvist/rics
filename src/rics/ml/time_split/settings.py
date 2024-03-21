"""Global settings for the splitting logic."""

import typing as _t

from . import types as _tst


class auto_flex:  # noqa: N801
    """Configuration for the `'auto'` :attr:`~rics.ml.time_split.types.Flex` logic.

    This class determines how ``(lo, hi)``-tuples are expanded when flexible bounds are enabled.
    """

    SANITY_CHECK: bool = True
    """If ``True``, use original limits if flexed limits do not pass sanity checks."""

    @classmethod
    def set_level(
        cls,
        level: _t.Literal["hour", "day"],
        *,
        start_at: _tst.TimedeltaTypes,
        round_to: _tst.TimedeltaTypes,
        tolerance: _tst.TimedeltaTypes,
    ) -> None:
        """Set a :class:`Level` used by the auto-flex logic.

        Inputs are not verified until an actual split is made.

        Args:
            level: The level to set; `'hour'` or `'day'`.
            start_at: Span size at which this level starts.
            round_to: Frequency to round the range limits to.
            tolerance: Maximum amount by which to alter limits.

        Raises:
            AttributeError: For unknown `level` names.

        """
        if level not in {"hour", "day"}:
            raise AttributeError(f"Bad {level=}: Expected one of ('hour', 'day').")
        level_tuple = (start_at, round_to, tolerance)
        setattr(cls, level, level_tuple)

    class Level(_t.NamedTuple):
        """Level type used by :attr:`auto_flex`."""

        start_at: _tst.TimedeltaTypes
        """Span size at which this level starts."""

        round_to: _tst.TimedeltaTypes
        """Frequency to round the range limits to."""

        tolerance: _tst.TimedeltaTypes
        """Maximum amount by which to alter limits."""

    hour: Level = Level("6 hours", "hour", "15 min")
    """Conditions under which bounds are rounded to the nearest hour.

    Default setting:
        Round to hour if the total range is at least 6 hours, but do not move the bounds more than 15 minutes.
    """

    day: Level = Level("2 days", "day", "3 hours")
    """Conditions under which bounds are rounded to the nearest day.

    Default setting:
        Round to day if the total range is at least 2 days, but do not move the bounds more than 3 hours.
    """


class plot:  # noqa: N801
    """Global settings for the :func:`.time_split.plot`-function."""

    THOUSANDS_SEPARATOR: str = "'"
    """Separator to use when printing `bar_labels`."""
    THOUSANDS_SEPARATOR_CUTOFF: int = 10_000
    """Minimum value before `bar_labels` include a :attr:`THOUSANDS_SEPARATOR`."""
    ROW_UNIT: str = "rows"
    """Unit to append to the count when displaying number of rows on the bars."""

    DATA_LABEL: str = "Data"
    """Label of the blue bar."""
    FUTURE_DATA_LABEL: str = "Future data"
    """Label of the red bar."""

    DEFAULT_TIME_UNIT: str = "h"
    """Time unit to use by default when ``bar_labels=True`` and ``available=None``."""

    REMOVED_FOLD_STYLE: _t.ClassVar[dict[str, _t.Any]] = {
        "alpha": 0.35,
        "height": 0.6,
    }
    """Keyword arguments used to distinguish filtered folds when plotting with ``show_removed=True``.

    See :func:`matplotlib.pyplot.bar` for details.
    """


class log_split_progress:  # noqa: N801
    """Global settings for the :func:`.log_split_progress`-function."""

    FOLD_FORMAT: str = "'{start.auto}' <= [schedule: '{mid.auto}' ({mid:%A})] < '{end.auto}'"
    """Pretty-printed `fold`-key for other messages.

    * Only the ``start``, ``mid``, and ``end`` keys are available (see
      :attr:`~rics.ml.time_split.types.DatetimeSplitBounds`). You may use ``<key>.auto`` to format as a date when
      time is zero (this is the default).

    .. code-block:: python
       :caption: Sample output.

       '2021-12-30' <= [schedule: '2022-01-04' (Tuesday)] < '2022-01-04 18:00:00'
    """

    SECONDS_FORMATTER: str | _t.Callable[[float], str] = "rics.performance.format_seconds"
    """A callable ``(seconds) -> formatted_seconds``.

    Both ``seconds`` and ``formatted_seconds`` will be available to the :attr:`END_MESSAGE` message. If a string is
    given, the actual callable will be resolved using :func:`rics.misc.get_by_full_name`.
    """

    START_MESSAGE: str = "Begin fold {n}/{n_splits}: {fold}."
    """Message indicating that the current fold has been yielded to the user.

    Has access to all keys from the previous section, as well as:

    * The ``fold`` key (see :attr:`FOLD_FORMAT`), and
    * The ``n`` key, which is the 1-based position of the fold in `splits`, and
    * The ``n_folds`` key, which is just ``len(splits)``.

    .. code-block:: python
       :caption: Sample output.

        Begin fold 5/7: '2021-12-30' <= [schedule: '2022-01-04' (Tuesday)] < '2022-01-04 18:00:00'.
    """

    END_MESSAGE: str = "Finished fold {n}/{n_splits}: [schedule: '{mid.auto}' ({mid:%A})] after {formatted_seconds}."
    """Message indicating that the user is done with the current fold.

    Has access to all keys from the previous sections, as well as:

    * The ``seconds`` key, which is the (fractional) time the user spent in the fold, and
    * The ``formatted_seconds`` key, obtained using the :attr:`SECONDS_FORMATTER`.

    The value of ``seconds`` is obtained using :py:func:`time.perf_counter`.

    .. code-block:: python
       :caption: Sample output.

        Finished fold 5/7: [schedule: '2022-01-04' (Tuesday)] after 5m 21s.
    """

    AUTO_DATE_FORMAT = "%Y-%m-%d"
    """Short-form timestamp format_spec used by ``<key>.auto``."""
    AUTO_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    """Long-form timestamp format_spec used by ``<key>.auto``."""


class misc:  # noqa: N801
    """Miscellaneous settings that don't fit in any other namespace."""

    snap_to_end: bool = True
    """Controls alignment of timedelta-based splits.

    .. note::

       Active only when both `schedule` and `after` are :attr:`~rics.ml.time_split.types.TimedeltaTypes`.

    If ``True``, ensure that the `Future data` of the final fold ends at the rightmost edge of the available data range.
    Otherwise, alignment is determined by :func:`pandas.date_range`.
    """
