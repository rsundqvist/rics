==============
The Translator
==============
The ``Translator`` is the main entry point for all translation tasks. For a simple usage example, see the
:ref:`Translating IDs in 30 seconds` section.

.. autoclass:: rics.translation.Translator
   :noindex:

====================
Handling unknown IDs
====================
Untranslatable IDs are will be `None` by default. Both and alternative alternative translation format and default values
may be specified to handle IDs which weren't returned by the underlying fetcher. Alternative formats work just like
regular formats, but if any placeholders other than `id` are specified, these must be included in the default
translations. As an example, by copying the ``[unknown_ids.*]`` sections from `config.toml`_, we see that the output for
an unknown title with ID `"tt0043440"` is translated the way we specified it.

.. list-table::
   :widths: 20 70
   :header-rows: 1

   * - Actor
     - Debut Title
   * - nm0038172:Peter Aryans \*1918†2001
     - tt0063897:Floris (original: Floris) \*1969†1969
   * - nm0040962:Ugo Attanasio \*1887†1969
     - tt0043440:Title unknown (original: Original title unknown) \*?†?

.. hint::
    A simple `default_fmt` such as ``"{id} not translated"`` or just ``"unknown"`` may be enough, and will only
    fail if the fetcher is configured to fail for unknown IDs. Using one of these we could've skipped the
    ``default-translations`` section entirely in the example above.

======================
Fetching: SQL database
======================
Implementation based on SQLAlchemy. Any supported dialect should work out of the box, though drivers for your particular
dialect may need to be installed separately.

.. autoclass:: rics.translation.fetching.SqlFetcher
   :noindex:

=====================
Fetching: Local files
=====================
Implementation wrapping a pandas Read-function where file names are interpreted as `source` names. Most readers in
`pandas.io <https://pandas.pydata.org/docs/reference/io.html>`_ should work, though additional dependencies may
be required for some of them. Many of these functions do not actually require the file to be present on the local file
system, allowing translation data to be shared if stored centrally.

.. autoclass:: rics.translation.fetching.PandasFetcher
   :noindex:

==============================
Fetching: User implementations
==============================
The abstract base class may be inherited by users to customize all aspects of the fetching process. You will find the
API reference for this class below.

.. autoclass:: rics.translation.fetching.AbstractFetcher
   :noindex:

===================
Offline translation
===================
The :meth:`rics.translation.Translator.store`-method is used to fetch as much data as possible or needed (if sample data
is given). Once fetching is complete, the fetcher will be disconnected and discarded. Translations will be faster, but
may cause high memory consumption.

.. _config.toml:
    https://github.com/rsundqvist/rics/blob/master/jupyterlab/demo/sql-translation/config.toml
