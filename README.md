# Readme

<div align="center">

[![PyPI - Version](https://img.shields.io/pypi/v/rics.svg)](https://pypi.python.org/pypi/rics)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/rics.svg)](https://pypi.python.org/pypi/rics)
[![Tests](https://github.com/rsundqvist/rics/workflows/tests/badge.svg)](https://github.com/rsundqvist/rics/actions?workflow=tests)
[![Codecov](https://codecov.io/gh/rsundqvist/rics/branch/main/graph/badge.svg)](https://codecov.io/gh/rsundqvist/rics)
[![Read the Docs](https://readthedocs.org/projects/rics/badge/)](https://rics.readthedocs.io/)
[![PyPI - License](https://img.shields.io/pypi/l/rics.svg)](https://pypi.python.org/pypi/rics)

[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)


</div>


My personal little ML engineering library.

* GitHub repo: <https://github.com/rsundqvist/rics.git>
* Documentation: <https://rics.readthedocs.io>
* Free software: MIT

## Features

* Multivariate performance testing - [with plots!](https://rics.readthedocs.io/en/latest/utility-perftest.html)
* An extensible [ID translation suite](https://rics.readthedocs.io/en/latest/translation-quickstart.html), including SQL integration for retrival of data
* Various other utilities methods - 
  from [logging configuration](https://rics.readthedocs.io/en/latest/utility-logging.html)
  to [fetching data from the web](https://rics.readthedocs.io/en/latest/utility-data-download.html)
* Two-directional mapping implementation in `rics.mapping`

## Quickstart for development

### Notice
This project uses groups for extras dependencies, which is currently a **PRERELEASE** feature (slated for `1.2`). Assuming
poetry was installed the recommended way (see below), this can be done using:
```bash
curl -sSL https://install.python-poetry.org/ | python -
poetry self update --preview 1.2.0a2
```

### Setting up for local development
Assumes a "modern" version of Ubuntu (guide written under `Ubuntu 20.04.2 LTS`) with basic dev dependencies installed.

This project uses groups for extras dependencies. If installation fails, make sure that output from `poetry --version` 
is `1.2.0` or greater.

To get started, run the following commands:

1. Installing the latest version of Poetry
   ```bash
   curl -sSL https://install.python-poetry.org/ | python -
   ```

2. Installing the project
   ```bash
   git clone git@github.com:rsundqvist/rics.git
   cd rics
   poetry install --with dev-extras
   inv install-hooks
   ./run-invocations
   ```
   The last step is optional, but serves to verify that the project is ready-to-run.

### Registering the project on Codecov

Probably only for forking?
```bash
curl -Os https://uploader.codecov.io/latest/linux/codecov
chmod +x codecov
```

Visit https://app.codecov.io and log in, follow instructions to link the repo and get a token for private repos.
```bash
CODECOV_TOKEN="<from-the-website>"
inv coverage --fmt=xml
./codecov -t ${CODECOV_TOKEN}
```

## Credits

This package was created with [Cookiecutter][cookiecutter] and
the [fedejaure/cookiecutter-modern-pypackage][cookiecutter-modern-pypackage] project template.

[cookiecutter]: https://github.com/cookiecutter/cookiecutter

[cookiecutter-modern-pypackage]: https://github.com/fedejaure/cookiecutter-modern-pypackage
