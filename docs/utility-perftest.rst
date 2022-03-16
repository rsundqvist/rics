================================
Multivariate performance testing
================================
Run performance tests with multiple candidates data collections. Outputs a figure and a :class:`pandas.DataFrame` of
long-format raw data. For an example, see the `Select IN vs BETWEEN`_ notebook.

.. figure:: multivar-perftest.png

   A performance summary figure.

.. automethod:: rics.utility.perf.run_multivariate_test
   :noindex:

.. warning::
    By default, this function reports averages of all runs (repetitions), as opposed to the built-in :py:mod:`timeit`
    module which reports only the best result (in non-verbose mode).

.. _Select IN vs BETWEEN:
    https://github.com/rsundqvist/rics/blob/master/jupyterlab/perf-test/sql/In-vs-Between.ipynb
