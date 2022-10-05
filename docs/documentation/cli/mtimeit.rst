mtimeit
=======

The ``mtimeit`` CLI tool may be used to run multivariate performance tests. This program wraps
:meth:`rics.performance.run_multivariate_test`.

Synopsis
--------
Output when running ``mtimeit --help``.

.. command-output:: mtimeit --help

Example
-------
Output when running ``mtimeit --create``. This flag may be used to initialize working dummy implementations of the
required `candidates.py` and `test_data.py` modules.

.. command-output:: (mkdir /tmp/example && cd /tmp/example/ && (echo y | mtimeit --create))
   :shell:
   :caption: Run the --create toy example in a temporary folder.
   :name: Run the --create toy example in a temporary folder.

.. command-output:: (tree /tmp/example/ -L 1)
   :shell:
   :caption: Contents of /tmp/example/
   :name: Contents of /tmp/example/
