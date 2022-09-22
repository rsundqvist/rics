.. _mapping-primer:

Mapping primer
==============
There are two principal steps involved in the mapping procedure: The :ref:`Scoring procedure` (see
:meth:`Mapper.compute_scores <rics.mapping.Mapper.compute_scores>`) and the subsequent :ref:`Matching procedure` (see
:meth:`Mapper.to_directional_mapping <rics.mapping.Mapper.to_directional_mapping>`). The two are automatically combined
when using the :meth:`Mapper.apply <rics.mapping.Mapper.apply>`-function, though they may be invoked separately by users.

Scoring procedure
-----------------
.. |caption| raw:: html

  <p style="text-align:right; font-style: italic;">Colours mapped by <br> spectral distance (RGB).</p>

.. figure:: ../_images/mapping.png
   :width: 220
   :align: right

   |caption|

The steps presented here is the *hierarchical* order. It does not necessarily represent the actual order in which things
are computed.

1. Runtime overrides (type: :attr:`~rics.mapping.types.UserOverrideFunction`); set ``score = ∞`` for the desired
   match , and ``score = -∞`` for others [#f1]_.

2. Static overrides (type: ``dict`` or :attr:`~rics.utility.collections.dicts.InheritedKeysDict`); set ``score = ∞``
   for the desired match, and ``score = -∞`` for others [#f1]_.

3. Filtering (type: :attr:`~rics.mapping.types.FilterFunction`); set ``score = -∞`` for undesirable matches only.

4. If there are any Heuristics (type: :class:`~rics.mapping._heuristic_score.HeuristicScore`), apply..

    a. Short-circuiting (type: :attr:`~rics.mapping.types.FilterFunction`); reinterpret a ``FilterFunction`` such that
       the returned candidates (if any) are treated as overrides [#f1]_.

    b. Aliasing (type: :attr:`~rics.mapping.types.AliasFunction`); try to improve ``ScoreFunction`` accuracy by
       applying heuristics to the ``(value, candidates)``-argument pairs.

    c. Finally, select the best score at each stage (from no to all heuristics) for each pair.

5. Regular score (type: :attr:`~rics.mapping.types.ScoreFunction`); higher is better.

The final output of the scoring procedure is a score matrix (a pandas ``DataFrame``), where columns are candidates and
values make up the index.

.. csv-table:: Partial mapping scores for the :ref:`dvdrental` example.
   :file: dvdrental-scores.csv
   :header-rows: 1
   :stub-columns: 1

The full score matrix has over 100 values (rows). The table above contains a subset of 20. The ``'rental_date'`` value
can be seen having only negative-infinity matching scores. This is intentional; the database has no suitable table for
translating dates. Mapping would've most likely failed regardless, but explicitly stating that ``'rental_date'`` should
not be translated (by using a filter) is more efficient. More importantly, it is also clearer.

Matching procedure
------------------
Given precomputed match scores (see the section above), make as many matches as possible given a ``Cardinality``
restriction. These may be summarized as:

* :attr:`~rics.mapping.Cardinality.OneToOne` = *'1:1'*. Each value and candidate may be used at most once.
* :attr:`~rics.mapping.Cardinality.OneToMany` = *'1:N'*: Values have exclusive ownership of matched candidate(s).
* :attr:`~rics.mapping.Cardinality.ManyToOne` = *'N:1'*: Ensure that as many values as possible are *unambiguously*
  mapped (i.e. to a single candidate). This is the **default option** for new ``Mapper`` instances.
* :attr:`~rics.mapping.Cardinality.ManyToMany` = *'M:N'*: All matches above the score limit are kept.

In theory, ``OneToMany`` and ``ManyToOne`` are equally restrictive. During mapping however, the goal is usually to
**find matches for the values**, not candidates. With that in mind, the ordering above may considered strictly decreasing
in preciseness.

Troubleshooting
---------------
Unmapped values are allowed by default. If mapping failure is not an acceptable outcome for your application, initialize
the ``Mapper`` with ``unmapped_values_action='raise'`` to ensure that an error is raised for unmapped values.

Mapper ``.details``-messages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The ``'rics.mapping.Mapper.accept.details'`` and ``'rics.mapping.Mapper.unmapped.details'`` loggers emit per-combination
mapping scores when matches are made (`accept.details`), or when values are left without a match (`unmapped.details`).
Records from these loggers are always emitted on the debug-level.

.. code-block:: python
    :caption: The ``'rics.mapping.Mapper.accept.details'``-logger lists matches that were rejected in favour of the current match.

    rics.mapping.Mapper.accept: Accepted: 'b' -> 'b'; score=1.000 >= 0.1.
    rics.mapping.Mapper.accept.details: This match supersedes 4 other matches:
      'b' -> 'ab'; score=0.500 (superseded on value='b').
      'b' -> 'a'; score=0.000 < 0.1 (below threshold).
      'b' -> 'fixed'; score=0.000 < 0.1 (below threshold).
      'a' -> 'b'; score=-inf (superseded by short-circuit or override).
    rics.mapping.Mapper: Match selection with cardinality='OneToOne' completed in 0.00369605 sec.

.. code-block:: python
   :caption: The ``'rics.mapping.Mapper.unmapped.details'``-logger explains why values were left unmapped.

    rics.mapping.Mapper.unmapped.details: Could not map value='is_nice':
      'is_nice' -> 'name'; score=0.125 < 1.0 (below threshold).
      'is_nice' -> 'gender'; score=0.083 < 1.0 (below threshold).
      'is_nice' -> 'id'; score=0.000 < 1.0 (below threshold).
    rics.mapping.Mapper.unmapped: Could not map {'is_nice'} in context='humans' to any of candidates={'name', 'gender', 'id'}.

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

.. [#f1] Exactly how other scores are adjusted depends on cardinality. The last override applied takes priority when
         conflicting overrides are defined.
