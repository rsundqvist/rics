"""Create temporal k-folds for cross-validation with heterogeneous data.

.. minigallery:: rics.ml.time_split.plot
    :add-heading: Examples
    :heading-level: =

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

By default, the bounds derived from `available` data is flexible. See :attr:`~rics.ml.time_split.types.Flex` for
details.

Restrictions:
    * **Data** and **Future data** from different folds may overlap, depending on the split parameters.
    * Date restrictions apply only to ``min(available), max(available)``. If there are gaps in the data, some folds may
      contain zero rows.
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

* Unbounded schedules. These must be made bounded by a `data` argument.

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

Use of all of these are demonstrated in the examples section.

.. _TimeSeriesSplit: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html

Available data `flex`
---------------------
Data :attr:`~rics.ml.time_split.types.Flex` allows bounds inferred from and `available` data argument to stretch outward
slightly. This useful in situations where the data is open of the left side only, or when data is sparse enough that
there aren't always records at exactly ``YYYY-mmm-dd 00:00:00``. Consider the following scenario:

.. code-block:: python

   schedule_timestamp = "2022-01-08 00:00:00"
   before, after = ("7d", "1d")
   final_timestamp_in_dataset = "2022-01-08 23:59:55"

Without `flex`, the `schedule_timestamp` above is invalid since there isn't enough `after` data to get one day of data
after the current `schedule_timestamp`. Using `flex` allows the splitter to stretch to ``2022-08-09 00:00:00``, yielding
the fold:

.. code-block:: python

   ('2022-01-01' <= [schedule: '2022-01-08' (Saturday)] < '2022-01-09')

This function is enabled by default since the scenario above is common. Set ``flex=False`` to disable.
"""
from ._frontend import log_split_progress, plot, split

__all__ = [
    "split",
    "plot",
    "log_split_progress",
]
