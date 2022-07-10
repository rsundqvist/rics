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

## Setting up for local development
Assumes a "modern" version of Ubuntu (guide written under `Ubuntu 20.04.2 LTS`) with basic dev dependencies installed.

To get started, run the following commands:

1. Installing Poetry and Invoke
   ```bash
   curl -sSL https://install.python-poetry.org/ | python -
   pip install invoke
   ```

2. Installing the project
   ```bash
   git clone git@github.com:rsundqvist/rics.git
   cd rics
   poetry install -E translation -E plotting
   inv install-hooks
   ./run-invocations.sh
   ```
   
    The last step is optional, but serves to verify that the project is ready-to-run.

## Credits

This package was created with [Cookiecutter][cookiecutter] and
the [fedejaure/cookiecutter-modern-pypackage][cookiecutter-modern-pypackage] project template.

[cookiecutter]: https://github.com/cookiecutter/cookiecutter
[cookiecutter-modern-pypackage]: https://github.com/fedejaure/cookiecutter-modern-pypackage
