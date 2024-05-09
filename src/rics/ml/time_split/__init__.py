"""Create temporal k-folds for cross-validation with heterogeneous data.

.. warning::

   This module is deprecated. Use the :mod:`time_split` |pypi-badge| package instead.

.. |pypi-badge| image:: https://img.shields.io/pypi/v/time-split.svg
                :target: https://pypi.org/project/time-split/

.. _tsug:

User guide
==========
High-level overview of relevant concepts.

Specification
-------------
A single fold is a 3-tuple of `bounds` ``(start, mid, end)``, see :attr:`~types.DatetimeSplitBounds`. A list thereof
are called `'splits'`, and have type :attr:`~types.DatetimeSplits`.

Conventions:
    - The **'mid'** timestamp is assumed to be the (simulated) training date, and
    - **Data** is restricted to ``start <= data.timestamp < mid``, and
    - **Future data** is restricted to ``mid <= future_data.timestamp < end``.

Guarantees:
    * Splits are strictly increasing: For all indices ``i``,  ``splits[i].mid < splits[i+1].mid`` holds.
    * Timestamps within a fold are strictly increasing: ``start[i] < mid[i] < end[i]``.
    * If `available` data is given **and** ``flex=False``, no part of any fold will lie outside the available range.

By default, the bounds derived from `available` data is flexible. See :ref:`Available data `flex`` for details.

Limitations:
    * **Data** and **Future data** from different folds may overlap, depending on the split parameters.
    * Date restrictions apply to ``min(available), max(available)``. Sparse data may create empty folds.
    * :attr:`~types.Schedule` and :attr:`~types.Span` arguments (before/after) must be strictly positive.

Schedules
---------
There are two types of :attr:`~rics.ml.time_split.types.Schedule`; bounded and unbounded. Any collection will be
interpreted as a bounded schedule. Unbounded schedules are either `cron` expressions, or a pandas
:ref:`offset alias <pandas:timeseries.offset_aliases>`.

* Bound schedules. These are always viable.

  >>> import pandas
  >>> schedule = ["2022-01-03", "2022-01-07", "2022-01-10", "2022-01-14"]
  >>> another_schedule = pandas.date_range("2022-01-01", "2022-10-10")

* Unbounded schedules. These must be made bounded by an `available` data argument.

  >>> cron_schedule = "0 0 * * MON,FRI"  # Monday and friday at midnight
  >>> offset_alias_schedule = "5d"  # Every 5 days

Bounded schedules are sometimes referred to as explicit schedules.

`Before` and `after` arguments
------------------------------
The `before` and `after` :attr:`~rics.ml.time_split.types.Span` arguments determine how much data is included in the
**Data** (given by `before`)  and **Future data** (given by `after`) ranges of each fold.

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Argument type
     - Interpretation
   * - String ``'all'``
     - Include all data before/after the scheduled time. Equivalent to ``max_train_size=None`` when using
       `TimeSeriesSplit`_.
   * - ``int > 0``
     - Include all data within `N` schedule periods from the scheduled time.
   * - Anything else
     - Passed as-is to the :class:`pandas.Timedelta` class. Must be positive. See
       :ref:`pandas:timeseries.offset_aliases` for valid frequency strings.

.. _TimeSeriesSplit: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html

Available data `flex`
---------------------
Data :attr:`~rics.ml.time_split.types.Flex` allows bounds inferred from and `available` data argument to stretch
**outward** slightly, toward the likely "real" limits of the data.

.. hint::

    See :func:`.support.expand_limits` for examples and manual experimentation.

.. list-table:: Flex options.
   :header-rows: 1
   :widths: 20 80

   * - Type
     - Description
   * - ``False``
     - Disable flex; use real limits instead.
   * - ``True`` or ``'auto'``
     - Auto-flex using :attr:`settings.auto_flex <rics.ml.time_split.settings.auto_flex>`-settings.

       Snap limits to the nearest :attr:`~.settings.auto_flex.hour` or :attr:`~.settings.auto_flex.day`, depending on
       the amount of `available` data. Use :meth:`settings.auto_flex.set_level <.settings.auto_flex.set_level>` to
       modify auto-flex behavior.

   * - ``str``
     - Manual flex specification.

       Pass an :ref:`offset alias <pandas:timeseries.offset_aliases>` specify how limits should be rounded. To specify
       by `how much` limits may be rounded, pass two offset aliases separated by a  ``'<'``.

       For example, passing ``flex="d<1h"`` will snap limits to the nearest date, but will not expand limits by more
       than one hour in either direction.
"""

from warnings import warn as _warn

from ._frontend import log_split_progress, plot, split

__all__ = [
    "log_split_progress",
    "plot",
    "split",
]

_warn(
    (
        f"The `{__package__}` submodule is now a stand-alone package.\n"
        "Run `python -m pip install time-split` to install, or"
        " pin `rics==4.0.1` to hide this warning."
    ),
    category=DeprecationWarning,
    stacklevel=2,
)
del _warn
