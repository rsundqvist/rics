.. _mapping-primer:

Mapping primer
==============
The main entry point for mapping tasks is the :class:`rics.mapping.Mapper` class. Mapping is used extensively by the
:ref:`translation <translation-primer>` package suite.

There are two principal steps involved in the mapping procedure: The :ref:`Scoring procedure` (see
:meth:`Mapper.compute_scores <rics.mapping.Mapper.compute_scores>`) and the subsequent :ref:`Matching procedure` (see
:meth:`Mapper.to_directional_mapping <rics.mapping.Mapper.to_directional_mapping>`). The two are automatically combined
when using the :meth:`Mapper.apply <rics.mapping.Mapper.apply>`-function, though they may be invoked separately by users.

Scoring procedure
-----------------
The ``Mapper`` first applies :ref:`Overrides and filtering`, after which the actual :ref:`Score computations` are
performed.

.. |caption| raw:: html

  <p style="text-align:right; font-style: italic;">Colours mapped by <br> spectral distance (RGB).</p>

.. figure:: ../_images/mapping.png
   :width: 220
   :align: right

   |caption|

Overrides and filtering
~~~~~~~~~~~~~~~~~~~~~~~
Overrides and filtering adhere to a strict hierarchy (the one presented below). Overrides take precedence over filters,
and runtime overrides takes precedence over static overrides.

1. Runtime overrides (type: :attr:`~rics.mapping.types.UserOverrideFunction`); set ``score=∞`` for the chosen candidate,
   and ``score=-∞`` for others.

2. Static overrides (type: ``dict`` or :attr:`~rics.utility.collections.dicts.InheritedKeysDict`); set ``score=∞`` for
   the chosen candidate, and ``score=-∞`` for others.

3. Filtering (type: :attr:`~rics.mapping.types.FilterFunction`); set ``score=-∞`` for undesirable matches only.

Score computations
~~~~~~~~~~~~~~~~~~
4. Compute value-candidate match scores (type: :attr:`~rics.mapping.types.ScoreFunction`). Higher is better.

5. If there are any Heuristics (type: :class:`~rics.mapping._heuristic_score.HeuristicScore`), apply..

    a. Short-circuiting (type: :attr:`~rics.mapping.types.FilterFunction`); reinterpret a ``FilterFunction`` such that
       the returned candidates (if any) are treated as overrides.

    b. Aliasing (type: :attr:`~rics.mapping.types.AliasFunction`); try to improve ``ScoreFunction`` accuracy by
       applying heuristics to the ``(value, candidates)``-argument pairs.

    c. Finally, select the best score at each stage (from no to all heuristics) for each pair.

The final output is a score matrix (type: :class:`pandas.DataFrame`), where columns are candidates and values make up
the index.

.. csv-table:: Partial mapping scores for the :ref:`dvdrental` example.
   :file: dvdrental-scores.csv
   :header-rows: 1
   :stub-columns: 1

The ``'rental_date'``-value can be seen having only negative-infinity matching scores due to filtering. Mapping would've
likely failed for this value regardless, but using explicit filters clearly indicates that translation is not wanted.

.. hint::

   The :meth:`Translator.map_scores <rics.translation.Translator.map_scores>`-method returns name-to-source match scores.

Matching procedure
------------------
Given precomputed match scores (see the section above), make as many matches as possible given a ``Cardinality``
restriction. These may be summarized as:

* :attr:`~rics.mapping.Cardinality.OneToOne` = *'1:1'*: Each value and candidate may be used at most once.
* :attr:`~rics.mapping.Cardinality.OneToMany` = *'1:N'*: Values have exclusive ownership of matched candidate(s).
* :attr:`~rics.mapping.Cardinality.ManyToOne` = *'N:1'*: Ensure that as many values as possible are *unambiguously*
  mapped (i.e. to a single candidate). This is the **default option** for new ``Mapper`` instances.
* :attr:`~rics.mapping.Cardinality.ManyToMany` = *'M:N'*: All matches above the score limit are kept.

In theory, ``OneToMany`` and ``ManyToOne`` are equally restrictive. During mapping however, the goal is usually to
find **matches for values**, not candidates. With that in mind, the ordering above may considered strictly decreasing
in preciseness.

Conflict resolution
~~~~~~~~~~~~~~~~~~~
When a single match out of multiple viable options must be chosen due to cardinality restrictions, priority is
determined by the iteration order of `values` and `candidates`. The first value will prefer the first candidate, and so
on. This logic does `not` consider future matches.

>>> mapper = Mapper(cardinality='1:1', score_function=lambda value, *_: [1, 0] if value == 'v1' else [1, 1])
>>> mapper.compute_scores(['v0', 'v1'], ['c0', 'c1'])
candidates   c0   c1
values
v0          1.0  1.0
v1          0.0  1.0
>>> mapper.apply(['v0', 'v1'], ['c0', 'c1']).flatten()
{'val0': 'cand0'}

Notice that `val1` was left without a match, even though it could've been assigned to `cand0` if the equally viable
matching `val0 → cand1` had been chosen first.

Troubleshooting
---------------
Unmapped values are allowed by default. If mapping failure is not an acceptable outcome for your application, initialize
the ``Mapper`` with ``unmapped_values_action='raise'`` to ensure that an error is raised for unmapped values, along with
more detailed log messages which are emitted on the error level.

Mapper ``.details``-messages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The ``'rics.mapping.Mapper.accept.details'`` and ``'rics.mapping.Mapper.unmapped.details'`` loggers emit per-combination
mapping scores when matches are made (`accept.details`), or when values are left without a match (`unmapped.details`).
Records from these loggers are always emitted on the debug-level.

.. code-block:: python
    :caption: The ``'rics.mapping.Mapper.accept.details'``-logger lists matches that were rejected in favour of the current match.

    rics.mapping.Mapper.accept: Accepted: 'v0' -> 'c0'; score=1.000 >= 1.0.
    rics.mapping.Mapper.accept.details: This match supersedes 2 other matches:
        'v0' -> 'c1'; score=1.000 (superseded on value='v0').
        'v1' -> 'c0'; score=1.000 (superseded on candidate='c0').

.. code-block:: python
   :caption: The ``'rics.mapping.Mapper.unmapped.details'``-logger explains why values were left unmapped.

    rics.mapping.Mapper.unmapped.details: Could not map value='v1':
        'v1' -> 'c0'; score=1.000 (superseded on candidate='c0': 'v0' -> 'c0'; score=1.000).
        'v1' -> 'c1'; score=0.000 < 1.0 (below threshold).

Unlike the ``unmapped.details``-logger, the level of the records emitted by its parent (the ``unmapped``-logger) is
determined by the :attr:`Mapper.unmapped_values_action <rics.mapping.Mapper.unmapped_values_action>`-attribute (
``'ignore'`` emits on the debug-level).

Verbose messages
~~~~~~~~~~~~~~~~
If ``.details``-logging is not enough, the last resort (before opening a debugger) is to enable verbose logging. The
recommended way of doing this is by using the :meth:`~rics.mapping.support.enable_verbose_debug_messages`-method, which
acts as a context manager.

.. code-block:: python

   from rics.mapping import Mapper, support
   with support.enable_verbose_debug_messages():
       Mapper(<config>).apply(<values>, <candidates>)

Verbose mode enables debug-level log messages from individual functions involved in the decision making and mapping
procedure, describing the internal operation of the ``Mapper`` in great detail.

.. code-block:: python
   :caption: A few verbose messages.

   rics.mapping.Mapper.accept: Accepted: 'a' -> 'ab'; score=inf (short-circuit or override).
   rics.mapping.filter_functions.require_regex_match: Refuse matching for name='a': Matches pattern=re.compile('.*a.*', re.IGNORECASE).
   rics.mapping.HeuristicScore: Heuristics scores for value='staff_id': ['store': 0.00 -> 0.50 (+0.50), 'payment': 0.07 -> 0.07 (+0.00), 'inventory': 0.00 -> 0.07 (+0.07), 'language': 0.00 -> 0.08 (+0.08), 'category': 0.00 -> 0.04 (+0.04), 'film': 0.05 -> 0.10 (+0.05), 'address': 0.00 -> 0.08 (+0.08), 'rental': 0.00 -> 0.08 (+0.08), 'customer_list': 0.00 -> 0.02 (+0.02), 'staff': 0.00 -> 1.00 (+1.00), 'staff_list': 0.00 -> 0.03 (+0.03), 'city': 0.00 -> 0.10 (+0.10), 'country': 0.00 -> 0.06 (+0.06), 'customer': 0.00 -> 0.04 (+0.04), 'actor': 0.00 -> 0.17 (+0.17)]
   rics.mapping.filter_functions.require_regex_match: Refuse matching for name='return_date': Does not match pattern=re.compile('.*_id$', re.IGNORECASE).

To permanently enable verbose logging, initialize with ``enable_verbose_logging=True``.

.. warning::

   Verbose mode may emit a large number of records and should be avoided except when required. For that reason, using
   ``enable_verbose_logging`` is not recommended.

.. rubric:: Footnotes
