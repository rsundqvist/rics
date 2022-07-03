
============================
Example: DVD Rental Database
============================
This example translates a query from the `DVD Rental Sample Database`_. It covers most of the more advanced features
that have been implemented. Using Docker, this database can be obtained by running:

.. code-block::

   docker run -p 5001:5432 moertel/postgresql-sample-dvdrental@sha256:e35f8dc4011d053777631208c85e3976a422b65e12383579d8a856a7849082c5

from the terminal. To describe the database, run

.. code-block::

   psql -h localhost -p 5001 -U postgres -d dvdrental -c "\d+"

from a separate terminal window. Leave out the last part (``-c "\d+"``) to query the database manually. We will use a
small query to describe rental transactions in the database:

.. literalinclude:: ../../tests/translation/dvdrental/query.sql
   :language: sql
   :caption: Query returning DVD rental transactions.
   :linenos:

The query above shows who rented what and when, what store they rented from and from whom.

.. csv-table:: Randomly sampled rows from the query. The first column is the record index in the query.
   :file: dvdrental.csv
   :header-rows: 1

The database has a few quirks, managed by :download:`this <../../tests/translation/dvdrental/translation.toml>`
translation configuration file and a :download:`separate file <../../tests/translation/dvdrental/sql-fetcher.toml>` for
access to the SQL database.

.. literalinclude:: ../../tests/translation/dvdrental/translation.toml
   :language: toml
   :caption: Translation configuration, mapping, and definition of the categories.
   :linenos:

.. literalinclude:: ../../tests/translation/dvdrental/sql-fetcher.toml
   :language: toml
   :caption: Configuration for fetching SQL data.
   :linenos:

.. note::

   See :doc:`../translation-config-format` for configuration file details.

Translating now becomes a simple matter. The following snippet is a test case which translates all of the ~16000 rows
returned by the query, verifying a random sample of 5 rows.


.. literalinclude:: ../../tests/translation/dvdrental/test_dvdrental.py
   :language: python
   :linenos:

The translated rows are:

.. csv-table:: The rows translated. Dates are not translated, nor is the first (row number/index) column.
   :file: ../../tests/translation/dvdrental/translated.csv
   :header-rows: 1

.. _DVD Rental Sample Database:
    https://www.postgresqltutorial.com/postgresql-getting-started/postgresql-sample-database/
.. _Covid cases:
    https://www.ecdc.europa.eu/en/publications-data/download-todays-data-geographic-distribution-covid-19-cases-worldwide
