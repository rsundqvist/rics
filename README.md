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

## What is it?
An assorted collection of reusable functions that used to live in a Dropbox folder. RiCS, pronounced _"rix_", is short 
for _**Ri**chard's **C**ode **S**tash_. I started this project with the purpose of learning more about Python best 
practices, typing and the Python ecosystem.

It has grown organically since then, and now provides a wide variety of small utility functions. Large submodules are
typically converted to [stand-alone PyPI packages](#related-libraries) once they begin to mature.

## Highlighted Features
- Multivariate [performance testing][perf] and [plotting][perf-plot].
- [get_by_full_name()]: Import functions, objects and classes by name.
- [rics.collections.dicts]: Extended functionality for the built-in `dict` type.
- [basic_config()]: Configure logging for development.
- And much more; click [here](https://rics.readthedocs.io/en/stable/api/rics.html) for the full API.

## Related libraries
The following packages started life as RiCS submodules.

* ID Translation
  [![PyPI - Version](https://img.shields.io/pypi/v/id-translation.svg)](https://pypi.python.org/pypi/id-translation) 
  [![Read the Docs](https://readthedocs.org/projects/id-translation/badge/)](https://id-translation.readthedocs.io/)
  [![Cookiecutter template](https://img.shields.io/badge/cookiecutter-template-red?logo=Cookiecutter)](https://github.com/rsundqvist/id-translation-project?tab=readme-ov-file#id-translation-cookiecutter-template)

  **_Turn meaningless IDs into human-readable labels._**

* Time Split
  [![PyPI - Version](https://img.shields.io/pypi/v/time-split.svg)](https://pypi.python.org/pypi/time-split)
  [![Read the Docs](https://readthedocs.org/projects/time-split/badge/)](https://time-split.readthedocs.io/)
  [![Docker Image Size (tag)](https://img.shields.io/docker/image-size/rsundqvist/time-split/latest?logo=docker&label=time-split)](https://hub.docker.com/r/rsundqvist/time-split/)

  **_Time-based k-fold validation splits for heterogeneous data._**

[perf]: https://rics.readthedocs.io/en/stable/api/rics.performance.html#rics.performance.run_multivariate_test
[perf-plot]: https://rics.readthedocs.io/en/stable/api/rics.performance.html#rics.performance.plot_run

[get_by_full_name()]: https://rics.readthedocs.io/en/stable/api/rics.misc.html#rics.misc.get_by_full_name

[basic_config()]: https://rics.readthedocs.io/en/stable/api/rics.logs.html#rics.logs.basic_config
[rics.collections.dicts]: https://rics.readthedocs.io/en/stable/api/rics.collections.dicts.html

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

## Command line program
The `rics` CLI is bundled with the package. Some [related libraries](#related-libraries) will add new subroutines. To 
get an overview, run:
```bash
rics --help
```
in the terminal.

## Contributing

All contributions, bug reports, bug fixes, documentation improvements, enhancements, and ideas are welcome. To get 
started, see the [Contributing Guide](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md).

[Python Package Index (PyPI)]: https://pypi.org/project/rics
[pip]: https://pip.pypa.io
[Python installation guide]: http://docs.python-guide.org/en/stable/starting/installation/
