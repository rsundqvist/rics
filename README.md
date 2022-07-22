<div align="center">
  <img src="https://github.com/rsundqvist/rics/raw/master/docs/logo-text.png"><br>
</div>

-----------------

# rics: my personal little ML engineering library. <!-- omit in toc -->
[![PyPI - Version](https://img.shields.io/pypi/v/rics.svg)](https://pypi.python.org/pypi/rics)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/rics.svg)](https://pypi.python.org/pypi/rics)
[![Tests](https://github.com/rsundqvist/rics/workflows/tests/badge.svg)](https://github.com/rsundqvist/rics/actions?workflow=tests)
[![Codecov](https://codecov.io/gh/rsundqvist/rics/branch/main/graph/badge.svg)](https://codecov.io/gh/rsundqvist/rics)
[![Read the Docs](https://readthedocs.org/projects/rics/badge/)](https://rics.readthedocs.io/)
[![PyPI - License](https://img.shields.io/pypi/l/rics.svg)](https://pypi.python.org/pypi/rics)
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

## What is it?

A **collection of utility and convenience functions** that I've written and rewritten over the years, until they become
so general that it makes sense to have them **documented and tested** for inclusion in the library. The scope is
naturally diverse and ranges from basic enum definitions to multivariate performance testing. More advanced features, 
like element mapping and ID translation, is built on top of basic utilities.

## Highlighted Features

- Multivariate [**performance testing**][perf].

- Highly configurable [**element mapping**][mapping] using a wide variety of filtering, scoring and heuristic functions.
 
- A flexible [**ID translation suite**][translation]: Converts meaningless IDs to
  human-readable labels. Comes with prebuilt [SQL][sql-fetcher] and 
  [file-system integration][pandas-fetcher], all of which is configurable using 
  [TOML][translator-config] files.

- Various other [**utilities**][utility], ranging from [logging] to [plotting] to specialized [dict] functions.

[perf]: https://rics.readthedocs.io/en/latest/_autosummary/rics.performance.html#rics.performance.run_multivariate_test
[perf-plot]: https://rics.readthedocs.io/en/latest/_autosummary/rics.performance.html#rics.performance.plot_run

[mapping]: https://rics.readthedocs.io/en/latest/_autosummary/rics.mapping.html

[translation]: https://rics.readthedocs.io/en/latest/_autosummary/rics.translation.html
[sql-fetcher]: https://rics.readthedocs.io/en/latest/_autosummary/rics.translation.fetching.html#rics.translation.fetching.SqlFetcher
[pandas-fetcher]: https://rics.readthedocs.io/en/latest/_autosummary/rics.translation.fetching.html#rics.translation.fetching.PandasFetcher
[translator-config]: https://rics.readthedocs.io/en/latest/documentation/translator-config.html

[utility]: https://rics.readthedocs.io/en/latest/_autosummary/rics.utility.html
[logging]: https://rics.readthedocs.io/en/latest/_autosummary/rics.utility.logs.html
[plotting]: https://rics.readthedocs.io/en/latest/_autosummary/rics.utility.plotting.html
[dict]: https://rics.readthedocs.io/en/latest/_autosummary/rics.utility.collections.dicts.html


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
[Python installation guide]: http://docs.python-guide.org/en/latest/starting/installation/
