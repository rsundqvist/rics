<div align="center">
  <img src="https://github.com/rsundqvist/rics/raw/master/docs/logo-text.png"><br>
</div>

-----------------

# RiCS: my personal little ML engineering library. <!-- omit in toc -->
[![PyPI - Version](https://img.shields.io/pypi/v/rics.svg)](https://pypi.python.org/pypi/rics)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/rics.svg)](https://pypi.python.org/pypi/rics)
[![Tests](https://github.com/rsundqvist/rics/workflows/tests/badge.svg)](https://github.com/rsundqvist/rics/actions?workflow=tests)
[![Codecov](https://codecov.io/gh/rsundqvist/rics/branch/master/graph/badge.svg)](https://codecov.io/gh/rsundqvist/rics)
[![Read the Docs](https://readthedocs.org/projects/rics/badge/)](https://rics.readthedocs.io/)
[![PyPI - License](https://img.shields.io/pypi/l/rics.svg)](https://pypi.python.org/pypi/rics)
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

## What is it?
An assorted collections of generic functions that used to live in a Dropbox folder where I used to keep useful snippets.
RiCS, pronounced _"rix_", is short for _**Ri**chard's **C**ode **S**tash_. I started this project with the purpose of 
learning more about Python best practices, typing and the Python ecosystem. It has grown organically since then, and now
provides a wide variety of utility functions. The [id-translation](https://pypi.org/project/id-translation/) suite 
(installed separately) relies heavily on [rics.mapping][mapping], as well as a number of other functions provided herein.

## Highlighted Features
- Multivariate [performance testing][perf].
- Highly configurable [element mapping][mapping];
  - Provides a wide variety of filtering, scoring and heuristic functions. 
  - Powers Name-to-source mapping for the [id-translation](https://id-translation.readthedocs.io/en/stable/documentation/translation-primer.html#name-to-source-mapping) 
    suite (installed separately).
- Various other [utilities][utility], ranging from [logging] to [plotting] to specialized [dict] functions.
- [Time-based cross-validation][time-split] splitter for heterogeneous data, 
  including ``pandas`` and ``scikit-learn`` integrations.

[perf]: https://rics.readthedocs.io/en/stable/_autosummary/rics.performance.html#rics.performance.run_multivariate_test
[perf-plot]: https://rics.readthedocs.io/en/stable/_autosummary/rics.performance.html#rics.performance.plot_run

[mapping]: https://rics.readthedocs.io/en/stable/_autosummary/rics.mapping.html

[utility]: https://rics.readthedocs.io/en/stable/_autosummary/rics.misc.html
[logging]: https://rics.readthedocs.io/en/stable/_autosummary/rics.logs.html
[plotting]: https://rics.readthedocs.io/en/stable/_autosummary/rics.plotting.html
[dict]: https://rics.readthedocs.io/en/stable/_autosummary/rics.collections.dicts.html
[time-split]: https://rics.readthedocs.io/en/stable/_autosummary/rics.ml.time_split.html

## Installation
The package is published through the [Python Package Index (PyPI)]. Source code
is available on GitHub: https://github.com/rsundqvist/rics

```sh
pip install -U rics
```

This is the preferred method to install ``rics``, as it will always install the
most recent stable release.

If you don't have [pip] installed, this [Python installation guide] can guide
you through the process.

## License
[MIT](LICENSE.md)

## Documentation
Hosted on Read the Docs: https://rics.readthedocs.io

## Contributing

All contributions, bug reports, bug fixes, documentation improvements, enhancements, and ideas are welcome. To get 
started, see the [Contributing Guide](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md).

[Python Package Index (PyPI)]: https://pypi.org/project/rics
[pip]: https://pip.pypa.io
[Python installation guide]: http://docs.python-guide.org/en/stable/starting/installation/
