"""Create temporal k-folds for cross-validation with heterogeneous data.

* :ref:`Example 1`: Cron schedule, keeping all data ``before`` the schedule.
* :ref:`Example 2`: List-schedule, without ``available`` data.
* :ref:`Example 3`: Timedelta-schedule, 5 days ``before``-data.
* :ref:`Example 4`: Removing folds with ``n_splits``. Dynamic ``before`` and ``after``-data.

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

  >>> from pandas import date_range
  >>> schedule = ["2022-01-03", "2022-01-07", "2022-01-10", "2022-01-14"]
  >>> another_schedule = date_range("2022-01-01", "2022-10-10")

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

Plotted examples
----------------
A picture is worth a thousand words.

>>> from rics import configure_stuff; configure_stuff()  # Make it pretty

Example 1
~~~~~~~~~
Using a `cron` schedule with data, showing number of rows in each partition.

>>> import pandas
>>> data = pandas.date_range("2022", "2022-1-21", freq="38min")
>>> plot("0 0 * * MON,FRI", before="all", after="3d", available=data)

.. image:: ../_images/folds-example1.png

The vertical, dashed lines shown denote the outer bounds of our `data`, beyond which the schedule may not extend.

Example 2
~~~~~~~~~
Using an explicit schedule without data, showing number of hours in each partition.

>>> schedule = ["2022-01-03", "2022-01-07", "2022-01-10", "2022-01-14"]
>>> plot(schedule, bar_labels="h")

.. image:: ../_images/folds-example2.png

Note that the last timestamp ('**2022-01-14**') of the schedule was not included; this is because it was used as the end
date (since ``after=1``) of the second-to-last timestamp ('**2022-01-10**'), which expands the **Future data** until the
next scheduled time.

Example 3
~~~~~~~~~
Using an unbounded timedelta-schedule, with custom bar labels.

>>> import pandas
>>> pandas.date_range("2022", "2022-1-21", freq="38min").to_series()
>>> bar_labels = [(f"{i}-left", f"{i}-right") for i in range(4)]
>>> plot("3d", before="5d", available=data, bar_labels=bar_labels)

.. image:: ../_images/folds-example3.png

Unbounded (timedelta) schedules require `available` data to materialize the schedule. When using the ``plot``-function,
this data is also used to create bar labels unless they're explicitly given, as seen above.

Example 4
~~~~~~~~~
Dynamic before/after-ranges, with removed partitions.

>>> import pandas
>>> data = pandas.date_range("2022", "2022-2", freq="15s")
>>> plot("0 0 * * MON,FRI", before=1, after=2, available=data,
... n_splits=4, show_removed=True)

.. image:: ../_images/folds-example4.png

Any non-zero integer before/after-range may be used. Setting ``show_removed=True`` forces plotting of folds that would
be silently discarded by the :func:`.split`-function. Later folds are preferred.
"""
from ._frontend import log_split_progress, plot, split

__all__ = [
    "split",
    "plot",
    "log_split_progress",
]
