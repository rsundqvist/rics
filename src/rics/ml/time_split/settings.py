"""Global settings for the splitting logic."""

import typing as _t


class plot:
    """Global settings for the :func:`.plot`-function."""

    THOUSANDS_SEPARATOR: str = "'"
    """Sign to use when printing `bar_labels`."""
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


class log_split_progress:
    """Global settings for the :func:`.log_split_progress`-function."""

    FOLD_FORMAT: str = "('{start.auto}' <= [schedule: '{mid.auto}' ({mid:%A})] < '{end.auto}')"
    """Pretty-printed `fold`-key for other messages.

    * Only the ``start``, ``mid``, and ``end`` keys are available (see
      :attr:`~rics.ml.time_split.types.DatetimeSplitBounds`). You may use ``<key>.auto`` to format as a date when
      time is zero (this is the default).

    .. code-block:: python
       :caption: Sample output.

       ('2021-12-30' <= [schedule: '2022-01-04' (Tuesday)] < '2022-01-04 18:00:00')
    """

    SECONDS_FORMATTER: _t.Union[str, _t.Callable[[float], str]] = "rics.performance.format_seconds"
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

        Begin fold 5/7: ('2021-12-30' <= [schedule: '2022-01-04' (Tuesday)] < '2022-01-04 18:00:00').
    """

    END_MESSAGE: str = "Finished fold {n}/{n_splits} [schedule: '{mid.auto}' ({mid:%A})] after {formatted_seconds}."
    """Message indicating that the user is done with the current fold.

    Has access to all keys from the previous sections, as well as:

    * The ``seconds`` key, which is the (fractional) time the user spent in the fold, and
    * The ``formatted_seconds`` key, obtained using the :attr:`SECONDS_FORMATTER`.

    The value of ``seconds`` is obtained using :py:func:`time.perf_counter`.

    .. code-block:: python
       :caption: Sample output.

        Finished fold 5/7 [schedule: '2022-01-04' (Tuesday)] after 5m 21s.
    """

    AUTO_DATE_FORMAT = "%Y-%m-%d"
    """Short-form timestamp format_spec used by ``<key>.auto``."""
    AUTO_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    """Long-form timestamp format_spec used by ``<key>.auto``."""
