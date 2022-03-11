ID Translation
==============
Turn meaningless IDs into human-readable labels.

======================
The Configuration File
======================
The recommended way of creating and configuring fetchers is the :meth:`rics.translation.Translator.from_config` method,
which takes a YAML config-file and returns a ready-run-run :class:`~rics.translation.Translator`. The translator has a
lot of configuration options, as does its components. See the `Translating with a SQL database`_ notebook and its
associated `config.yaml`_ file for an example.

=============================
Translating IDs in 30 seconds
=============================
We will assume that there is a PostgreSQL database running locally with the following two tables present::

    humans:                       animals:
       id | name    | Gender        bestie_id | name   | is_nice
    ------+---------+--------      -----------+--------+---------
     1991 | Richard | Male                  0 | Tarzan | false
     1999 | Sofia   | Female                1 | Morris | true
                                            2 | Simba  | true

What we need:
    * A :class:`~rics.translation.fetching.SqlFetcher` to fetch from the tables above.
    * A :class:`~rics.mapping.Mapper` to bind names (such as `human_id` to table `humans`) automatically.
    * Some :class:`~rics.translation.offline.PlaceholderOverrides` since the `animals` table has a strange ID column.

Putting it all together:

>>> from rics.translation import Translator
>>> from rics.translation.fetching import SqlFetcher
>>> from rics.translation.offline import PlaceholderOverrides
>>> from rics.mapping import Mapper
>>>
>>> fetcher = SqlFetcher(
...     # Connection string may be an environment variable if
...     # prefixed by '@'. Example: @TRANSLATION_DB_CONNECTION_STRING
...     connection_string = 'postgresql://user:passwrod@localhost:5432/mydatabase',
...     whitelist_tables = ['humans', 'animals'],
...     placeholder_overrides=PlaceholderOverrides(source_specific={'animals': {'bestie_id': 'id'}})
... )  # doctest: +SKIP
>>> mapper=Mapper(score_function='like_database_table', apply_heuristics=True, overrides={"people": "humans"})
>>> translator = Translator(fetcher, fmt='{id}:{name}[, nice={is_nice}]', mapper=mapper) # doctest: +SKIP
>>> data = {'animal': [0, 2], 'people': [1991, 1999]}
>>> for key, translated_table in translator.translate(data).items():
...    print(f'Translations for {repr(key)}:')
...    for translated_id in translated_table:
...        print(f'    {repr(translated_id)}') # Doctest: +SKIP
Translations for 'animal':
    '0:Tarzan, nice=False'
    '2:Simba, nice=True'
Translations for 'people':
    '1991:Richard'
    '1999:Sofia'

**Summary**:
    * Database contains tables `humans` and `animals`. Names are "animal" and "people".
    * ``PlaceholderOverrides``: The ID-column in `animals` is ``animals.bestie_id``, we expected ``id``.
    * ``Mapper``: Responsible for matching `animal` with table `animals`. The words `"people"` and `"humans"` are too
      different for :meth:`~rics.mapping.score_functions.like_database_table`, so we provide this binding.
    * The translator ties it all together when we call :meth:`~rics.translation.Translator.translate`.
    * There is no ``humans.is_nice`` column; ``nice=<True/False>`` is present only for animals.

The example above could be solved using config options that :meth:`Translator.from_config()
<rics.translation.Translator.from_config>` provides. The primary use case for importing and using these classes directly
is writing a more advanced a ``score_function`` or fetcher than the implementations of this package provide.

===================
Offline translation
===================
If you do not want to keep the fetcher connected to the database, you can use the translator
:meth:`~rics.translation.Translator.store`-method to fetch as much data as possible after which the fetcher will be
closed. A :class:`~rics.translation.offline.TranslationMap` will be stored for offline operation.
Uses a lot of memory for large tables.

==========================
Translation format strings
==========================
The :class:`rics.translation.offline.Format` class defines the string format. These are simlar to regular fstrings, with
two significant exceptions:

    a. Keyword placeholders only: ``'{}'`` is not accepted, correct form is ``'{key-name}}'``.
    b. Substrings surrounded by ``[]`` denote an optional element.

Examples:
    Importing the class and defining a string format with an optional element ``', nice={is_nice}'``:

    >>> from rics.translation.offline import Format
    >>> fmt = Format('{id}:{name}[, nice={is_nice}]')

    Only required placeholders are used by default..

    >>> fmt.fstring(), fmt.fstring().format(id=0, name='Tarzan')
    ('{id}:{name}', '0:Tarzan')

    ..but the `placeholders` attribute can be used to retrieve all placeholders, required and optional

    >>> fmt.placeholders
    ('id', 'name', 'is_nice')
    >>> fmt.fstring(fmt.placeholders), fmt.fstring(fmt.placeholders).format(id=1, name='Morris', is_nice=True)
    ('{id}:{name}, nice={is_nice}', '1:Morris, nice=True')

.. _Translating with a SQL database:
    https://github.com/rsundqvist/rics/jupyterlab/demo/sql-translation/SqlFetcher.ipynb
.. _config.yaml:
    https://github.com/rsundqvist/rics/jupyterlab/demo/sql-translation/config.yaml
