=====================
Logging configuration
=====================
Set up Python logging with sane defaults and an informative logging format.

.. automethod:: rics.utility.logs.basic_config
   :noindex:

--------------------------
Example Setting log levels
--------------------------
Set a different log level for `rics`.

>>> from rics.utility.logs import basic_config, logging
>>> root_logger = logging.getLogger()
>>> basic_config(level=logging.INFO, rics_level=logging.DEBUG)
>>> logging.getLogger("rics").debug("I'm a debug message!")
>>> root_logger.debug("I'm a debug message!")
>>> root_logger.critical("I'm a critical message!") # Doctest: +SKIP
2022-02-05T11:17:05.378 [rics:DEBUG] I'm a debug message!
2022-02-05T11:17:05.378 [root:CRITICAL] I'm a critical message!

If `rics_level` is not given, the root logger log level is inherited as expected.

>>> basic_config(level=logging.INFO)  # doctest: +SKIP
>>> logging.getLogger("rics").debug("I'm a debug message!")
>>> logging.getLogger("rics").debug("I'm a critical message!")  # doctest: +SKIP
2022-02-05T11:17:05.379 [rics:CRITICAL] I'm a critical message!

Specifying different log levels for other namespaces is done in the same way. Underscores may be used instead of
dots when specifying the module path.

>>> basic_config(
...     level=logging.CRITICAL,
...     rics_level=logging.INFO,
...     rics_submodule_level=logging.DEBUG,
...     lib_module_level=logging.WARNING,
... )
>>> logging.getLogger().warning("I'm a warning message!")
>>> logging.getLogger("rics").debug("I'm a debug message!")
>>> logging.getLogger("rics.submodule").debug("I'm a debug message!")
>>> logging.getLogger("lib.module").debug("I'm a debug message!")
>>> logging.getLogger("lib.module").warning("I'm a warning message!") # doctest: +SKIP
2022-02-05T11:17:05.379 [rics.submodule:DEBUG] I'm a debug message!
2022-02-05T11:17:05.379 [lib.module:WARNING] I'm a warning message!

The `logging`-module exposed is just the regular Python logging library.
