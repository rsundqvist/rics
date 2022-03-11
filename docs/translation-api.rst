==============
The Translator
==============
The ``Translator`` is the main entry point for all translation tasks.

.. autoclass:: rics.translation.Translator
   :noindex:

=============
Fetching data
=============

Fetching data is done using :class:`~rics.translation.fetching.Fetcher`-implementations.

-----------------------------------------
Fetching translations from a SQL database
-----------------------------------------
The default SQL fetcher uses SQLAlchemy. Any supported dialect should work out ouf the box.

.. autoclass:: rics.translation.fetching.SqlFetcher
   :noindex:

-------------------
Customized fetching
-------------------
The base class may be inherited by users to customize all aspects of the fetching process. You will find the
API reference for this class below. Overriding the abstract methods in this class will give you your own functional
fetcher implementation.

.. autoclass:: rics.translation.fetching.Fetcher
   :noindex:
