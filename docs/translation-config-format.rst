TOML Configuration
==================

The recommended way of creating and configuring fetchers is the :meth:`Translator.from_config()
<rics.translation.Translator.from_config>` method, which takes a TOML config-file and returns a ready-to-run
:class:`~rics.translation.Translator`.

The only valid top-level keys are ``translator``, ``unknown_ids``, and ``fetching``. Only the ``fetching`` section is
required, though it may be left out of the main configuration file if fetching is configured separately. Other top-level
keys will raise a :class:`~rics.translation.exceptions.ConfigurationError` if present.

**Examples**:
    * :doc:`examples/notebooks/sql-translation/SqlFetcher`,
      which uses :download:`this <examples/notebooks/sql-translation/config.toml>` config file.
    * :doc:`examples/notebooks/pickle-translation/PickleFetcher`,
      which uses :download:`this <examples/notebooks/pickle-translation/config.toml>` config file.
    * :doc:`examples/dvdrental` defines a :class:`~rics.translation.fetching.MemoryFetcher` in the main
      :download:`translation config <../tests/translation/dvdrental/translation.toml>` file, and a
      :class:`~rics.translation.fetching.SqlFetcher` (:download:`sql-fetcher.toml <../tests/translation/dvdrental/sql-fetcher.toml>`).
      The two are combined into a :class:`~rics.translation.fetching.MultiFetcher`.

Multiple fetchers
-----------------
Complex applications may require multiple fetchers. These may be specified in auxiliary config files, one fetcher per
file. Only the ``fetching`` key will be considered in these files. If multiple fetchers are defined, theses will be
combined into a :class:`~rics.translation.fetching.MultiFetcher`. Fetchers are considered in the order in which the
config files are given when resolving :attr:`~rics.translation.fetching.types.Fetcher.sources` during name-to-source
mapping, eg when translating data with a Translator created by running

>>> from rics.translation import Translator
>>> extra_fetchers=["fetcher.toml", "backup-fetcher.toml"]
>>> Translator.from_config("translation.toml", extra_fetchers=extra_fetchers)

the :func:`~rics.translation.Translator.map_to_sources`-function will first consider the sources of the
fetcher defined in **translation.toml** (if there is one), then the ones defined in `fetcher.toml` before finally
considering sources returned by the fetcher defined by `backup-fetcher.toml`.

Section: Translator
-------------------
.. list-table:: Section keys: ``[translator]``
   :header-rows: 1

   * - Key
     - Type
     - Description
     - Comments
   * - fmt
     - :class:`~rics.translation.offline.Format`
     - Specify how translated IDs are displayed
     - See :doc:`translation-format`

* Parameters for :attr:`Name <rics.translation.offline.types.NameType>`-to-:attr:`source <rics.translation.offline.types.SourceType>`
  mapping are specified in a ``[translator.mapping]``-subsection. See :ref:`Subsection: Mapping` for details (context =
  :attr:`source <rics.translation.offline.types.SourceType>`).

Section: Unknown IDs
--------------------
.. list-table:: Section keys: ``[unknown_ids]``
   :header-rows: 1

   * - Key
     - Type
     - Description
     - Comments
   * - fmt
     - :class:`~rics.translation.offline.Format`
     - Specify an format for untranslated IDs.
     - Can be a plain string ``fmt="Unknown"``, or ``fmt="{id}"`` to leave as-is.

* Alternative :attr:`placeholder <rics.translation.offline.Format.placeholders>`-values for unknown IDs can be declared
  in a ``[unknown_ids.overrides]``-subsection. See :ref:`Subsection: Overrides` for details (context =
  :attr:`source <rics.translation.offline.types.SourceType>`).

Section: Fetching
-----------------
.. list-table:: Section keys: ``[fetching]``
   :header-rows: 1

   * - Key
     - Type
     - Description
     - Comments
   * - allow_fetch_all
     - :py:class:`bool`
     - Control access to :func:`~rics.translation.fetching.types.Fetcher.fetch_all`.
     - Some fetchers types redefine or ignore this key.

* The :class:`~rics.translation.fetching.AbstractFetcher` class uses a :class:`~rics.mapping.Mapper` to bind
  actual :attr:`placeholder <rics.translation.fetching.types.Fetcher.placeholders>` names
  in :attr:`~rics.translation.fetching.types.Fetcher.sources`
  to desired :attr:`placeholder names <rics.translation.offline.Format.placeholders>` requested by the calling
  Translator instance. See :ref:`Subsection: Mapping` for details
  (context = :attr:`source <rics.translation.offline.types.SourceType>`).

Subsection: Mapping
-------------------
.. list-table:: Section keys: ``[*.mapping]``
   :header-rows: 1

   * - Key
     - Type
     - Description
     - Comments
   * - score_function
     - :attr:`~rics.mapping.score_functions.ScoreFunction`
     - Compute value/candidate-likeness
     - See :mod:`rics.mapping.score_functions`
   * - unmapped_values_action
     - `raise | warn | ignore`
     - Handle unmatched values.
     - See: :class:`rics.utility.action_level.ActionLevel`
   * - cardinality
     - `OneToOne | ManyToOne`
     - Determine how many candidates to map a single value to.
     - See: :class:`rics.cardinality.Cardinality`

* Score functions which take additional keyword arguments should instead be specified in a child section, eg
  ``[*.mapping.<score-function-name>]``. See :mod:`rics.mapping.score_functions` for options.

.. hint::

  Mappings that are difficult or impossible to make using automated scoring may be forced by using
  :ref:`overrides <Subsection: Overrides>` instead.


Filter functions
~~~~~~~~~~~~~~~~
Filter functions are used to remove undesirable matches, for example SQL tables which should not be used or DataFrame
columns names which should not be translated.

Filters are given in ``[[*.mapping.filter_functions]]`` **list**-subsections. These may be used to remove undesirable
matches, for example SQL tables which should not be used or DataFrame column names which should not be translated.

.. list-table:: Section keys: ``[[*.mapping.filter_functions]]``
   :header-rows: 1

   * - Key
     - Type
     - Description
     - Comments
   * - function
     - :py:class:`str`
     - Function name.
     - See: :mod:`rics.mapping.filter_functions`

.. note::

   Additional keys depend on the chosen function implementation.

As an example, the next snippet ensures that only names ending with an ``_id``-suffix will be translated by using a
:meth:`~rics.mapping.filter_functions.require_regex_match` filter.

.. code-block:: toml

    [[translator.mapping.filter_functions]]
    function = "require_regex_match"
    regex = ".*_id$"
    where = "name"


Score function
~~~~~~~~~~~~~~
There are some :attr:`~rics.mapping.score_functions.ScoreFunction` s which take additional keyword arguments. These must
be declared in a ``[*.overrides.<score-function-name>]``-subsection. See :mod:`rics.mapping.score_functions` for options.

Score function heuristics
~~~~~~~~~~~~~~~~~~~~~~~~~
Heuristics may be used to aid an underlying `score_function` to make more difficult matches. There are two types of
heuristic functions: :attr:`~rics.mapping.heuristic_functions.AliasFunction` s and Short-circuiting functions (which are
really just differently interpreted :attr:`~rics.mapping.filter_functions.FilterFunction` s).

Heuristics are given in ``[[*.mapping.score_function_heuristics]]`` **list**-subsections (note the double brackets) and
are applied in the order in which they are given by the :class:`~rics.mapping.HeuristicScore` wrapper
class.

.. list-table:: Section keys: ``[[*.mapping.score_function_heuristics]]``
   :header-rows: 1

   * - Key
     - Type
     - Description
     - Comments
   * - function
     - :py:class:`str`
     - Function name.
     - See: :mod:`rics.mapping.heuristic_functions`

.. note::

   Additional keys depend on the chosen function implementation.

As an example, the next snippet let's us match table columns such as `animal_id` to the `id` placeholder by using a
:meth:`~rics.mapping.heuristic_functions.value_fstring_alias` heuristic.

.. code-block:: toml

    [[fetching.mapping.score_function_heuristics]]
    function = "value_fstring_alias"
    fstring = "{context}_{value}"

.. note::

   For very difficult matches, consider using :ref:`overrides <Subsection: Overrides>` instead.

Subsection: Overrides
---------------------
Shared or context-specific key-value pairs implemented by the :class:`~rics.utility.collections.inherited_keys_dict.InheritedKeysDict`
class. When used in config files, these appear as ``[*.overrides]``-sections. Top-level override items are given in the
``[*.overrides]``-section, while context-specific items are specified using a subsection, eg
``[*.overrides.<context-name>]``.

.. note::

   The type of ``context`` is determined by the class that owns the overrides.

As an example, the next snippet forces the `from` and `to` placeholders to `"?"` for all :ref:`unknown IDs <Section: Unknown IDs>`
in the `IMDB Database <../jupyterlab/demo/pickle-translation/PickleFetcher.ipynb>`__, while the name is forced to be
`"Name unknown"` for the `"name_basics"` source and `"Title unknown"` for the `"title_basics"` source, respectively.
They both inherit the `from` and `to` keys.

.. code-block:: toml

    [unknown_ids.overrides]
    from = "?"
    to = "?"

    [unknown_ids.overrides.name_basics]
    name = "Name unknown"
    [unknown_ids.overrides.title_basics]
    name = "Title unknown"

.. warning::

   Overrides have no fixed keys. No validation is performed and errors may be silent. The
   :attr:`mapping process <rics.mapping.Mapper.apply>` provides detailed information in debug mode, which may be used to
   discover issues.

.. hint::

   Overrides may also be used to `prevent` mapping certain values.

For example, let's assume that a SQL source table called `title_basics` with two columns `title` and `name` with
identical contents. We would like to use a format ``"[{title}. ]{name}"`` to output translations such as
`"Mr. Astaire"`. To avoid output such as `"Top Hat. Top Hat"` for movies, we may add

.. code-block:: toml

  [fetching.mapping.overrides.movies]
  title = "_"

to force the fetcher to inform the Translator that the `title` placeholder (column) does not exist for the `title_basics`
source (we used `"_"` since TOML `does not have <https://github.com/toml-lang/toml/issues/30>`__ a ``null``-type).
