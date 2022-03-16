==============
The Translator
==============
The ``Translator`` is the main entry point for all translation tasks. For a simple usage example, see the
:ref:`Translating IDs in 30 seconds` section.

.. autoclass:: rics.translation.Translator
   :noindex:

To actually get the translations, a :class:`~rics.translation.fetching.Fetcher` implementation is needed.

====================
Default translations
====================
Default translations use a simple ``{source: {key: value}}`` format. For example, ``{"animals": {"can_fly": False}`` sets
the default value to False for any animal which is not present in the `animals` source. Shared translations are not
possible (yet, see `#31 <https://github.com/rsundqvist/rics/issues/31>`_).

======================
Fetching: SQL database
======================
Implementation based on SQLAlchemy. Any supported dialect should work out of the box, though drivers for your particular
dialect may need to be installed separately.

.. autoclass:: rics.translation.fetching.SqlFetcher
   :noindex:

==========================
Fetching: Local files
==========================
Implementation wrapping a pandas Read-function where file names are interpreted as `source` names. Most readers in
`pandas.io <https://pandas.pydata.org/docs/reference/io.html>`_ should work, though additional dependencies may
be required for some of them. Many of these functions do not actually require the file to be present on the local file
system, allowing translation data to be shared if stored centrally.

.. autoclass:: rics.translation.fetching.PandasFetcher
   :noindex:

==============================
Fetching: User implementations
==============================
The base class may be inherited by users to customize all aspects of the fetching process. You will find the
API reference for this class below.

.. autoclass:: rics.translation.fetching.Fetcher
   :noindex:

===================
Offline translation
===================
If you do not want to keep the fetcher connected to a database or the file system, you can use the translator
:meth:`~rics.translation.Translator.store`-method to fetch as much data as possible after which the fetcher will be
disconnected and discarded. Alternatively, you may supply a :class:`~rics.translation.offline.TranslationMap` as the
fetcher instance when initializing the translator. May cause high memory consumption.
