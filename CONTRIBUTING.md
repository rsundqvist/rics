# Contributing <!-- omit in toc -->

First of all, thank you for using and contributing to `rics`! Any and all contributions are welcome.

## Creating issues
Issues are tracked on [GitHub](https://github.com/rsundqvist/rics/issues). Issue
reports are appreciated, but please use a succinct title and add relevant tags.
Please include a [**Minimal reproducible example**][minimal-reproducible-example]
if reporting an issue, or sample snippet if requesting a new feature or change 
which demonstrates the (desired) usage.

[minimal-reproducible-example]: https://stackoverflow.com/help/minimal-reproducible-example

## PR guidelines
To be merged, all tests (including generating documentation), must be successful.

## Code requirements
General requirements which applies to all code in the library.

### Unchecked requirements
These requirements are *not* verified in CI/CD.

* User-facing changes should be recorded in the [changelog](https://github.com/rsundqvist/rics/blob/master/CHANGELOG.md).
* Summarize the changes being made, and why they're made.
* Expensive operations (especially related to logging) should only be done if the result is needed.
* Coverage exceptions should be minimal.

### Checked requirements
These requirements are verified in CI/CD.

* Coverage limit should not decrease unless it's well-motivated.
* Public methods and classes must be documented.
* Use the commit hooks to format and lint the code.

## Getting started
Follow these steps to begin local development. I use Ubuntu LTS and PyCharm 
(both are kept updated), so such environments will usually work without too much
trouble.

1. **Installing [Poetry](https://python-poetry.org/docs/) and [Invoke](https://www.pyinvoke.org/)**
   
   Poetry is a dependency management tool. You must have `poetry >= 1.2.2` as this project uses version 2.0 of the
   lockfile  format.
   ```bash
   curl -sSL https://install.python-poetry.org/ | python -
   pip install invoke
   ```

2. **Installing the project**
   
   Clone and install the virtual environment used for development. Some material
   is placed in submodules, so we need to clone recursively.
   ```bash
   git clone --recurse-submodules git@github.com:rsundqvist/rics.git
   cd rics
   poetry install --all-extras
   ```
   
   Generating documentation has a few dependencies which may need to be installed
   manually.
   ```bash
   sudo apt-get update
   sudo apt-get install pandoc tree
   ```
   
3. **Verify installation**

   This is similar to what the CI/CD pipeline will run for a single OS and major
   Python version. It also skips the additional isolation provided by `nox`,
   which may hide some dependency-gotchas.
   ```bash
   ./run-invocations.sh
   ```

### Running GitHub Actions locally
Relying on GitHub actions for new CI/CD features is quite slow. An alternative is to use 
[act](https://github.com/nektos/act) instead, which allows running pipelines locally (with some limitations, see `act` 
docs). For example, running

```shell
act -j tests
```

will execute the [tests](https://github.com/rsundqvist/rics/blob/master/.github/workflows/tests.yml) workflow.
