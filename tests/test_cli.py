from collections.abc import Mapping

import pandas as pd
import pytest
import responses
from click.testing import CliRunner, Result

from rics import cli


@responses.activate
def test_repos(monkeypatch):
    """Test case used mocked requests responses."""
    result = run(monkeypatch)

    assert result.exit_code == 0, result.stderr

    # Verify logging
    assert ":DEBUG] Found 30 repo(s) for user 1/1: 'astral-sh'." in result.stderr
    assert ":INFO] Processed 6/30 matching repos" in result.stderr
    assert result.stderr.count("no releases") == 15
    assert result.stderr.count("no licence") == 4
    assert result.stderr.count(" > max_days=7") == 5

    # Verify output table.
    assert result.stdout.removesuffix("\n") == expected.strip("\n")


@responses.activate
def test_verbose_1(monkeypatch):
    """Should override RICS_VERBOSE=4 in env."""
    result = run(monkeypatch, "-v")
    assert result.exit_code == 0, result.stderr

    # Verify logging
    assert "DEBUG" not in result.stderr
    assert ":INFO] Processed 6/30 matching repos" in result.stderr

    # Verify output table.
    assert result.stdout.removesuffix("\n") == expected.strip("\n")


expected = """
                      Release tag            Last push  Stars  Issues                                                                       Description                                      Link     License    Created
Repo name                                                                                                                                                                                                               
astral-sh/ruff             0.11.2 2025-04-01T17:47:13Z  37413    1484              An extremely fast Python linter and code formatter, written in Rust.         https://github.com/astral-sh/ruff         MIT 2022-08-09
astral-sh/uv               0.6.11 2025-04-01T17:09:06Z  47487    1568            An extremely fast Python package and project manager, written in Rust.           https://github.com/astral-sh/uv  Apache-2.0 2023-10-02
astral-sh/setup-uv         v5.4.1 2025-04-01T10:30:02Z    348      22  Set up your GitHub Actions workflow with a specific version of https://docs.astr     https://github.com/astral-sh/setup-uv         MIT 2024-08-23
astral-sh/rye              0.44.0 2025-03-31T00:28:22Z  14108     332                                                   a Hassle-Free Python Experience          https://github.com/astral-sh/rye         MIT 2023-04-22
astral-sh/packse           0.3.46 2025-03-27T20:11:10Z    115       9                                                        Python packaging scenarios       https://github.com/astral-sh/packse  Apache-2.0 2023-12-13
astral-sh/ruff-action      v3.2.2 2025-03-27T04:53:31Z    117       5                                                       A GitHub Action to run Ruff  https://github.com/astral-sh/ruff-action  Apache-2.0 2024-09-29
"""  # noqa


def run(monkeypatch: pytest.MonkeyPatch, verbose: str | None = None) -> Result:
    monkeypatch.setattr("pandas.Timestamp.utcnow", lambda: pd.Timestamp("2025-04-01", tz="utc"))
    _setup_requests()

    args = ["repos", "--max-days=7", "--max-width=80"]
    if verbose:
        args = [verbose, *args]

    return CliRunner().invoke(
        cli.main,
        args,
        env={"RICS_REPOS_USER": "astral-sh", "RICS_VERBOSE": "4"},
    )


def _setup_requests():
    responses.add(
        responses.GET,
        "https://api.github.com/users/astral-sh/repos",
        json=repos,
    )
    for repo in repos:
        name = repo["name"]
        assert isinstance(name, str)
        json = releases.get(name)
        responses.add(
            responses.GET,
            f"https://api.github.com/repos/astral-sh/{repo['name']}/latest",
            json=json,
            status=200 if json else 404,
        )


releases = {
    "packse": {"tag_name": "0.3.46"},
    "ruff": {"tag_name": "0.11.2"},
    "ruff-action": {"tag_name": "v3.2.2"},
    "ruff-lsp": {"tag_name": "v0.0.62"},
    "ruff-vscode": {"tag_name": "2025.22.0"},
    "python-build-standalone": {"tag_name": "20250317"},
    "ruff-pre-commit": {"tag_name": "v0.11.2"},
    "rye": {"tag_name": "0.44.0"},
    "tokio-tar": {"tag_name": "v0.5.2"},
    "setup-uv": {"tag_name": "v5.4.1"},
    "uv": {"tag_name": "0.6.11"},
}

repos: list[Mapping[str, str | int | dict[str, str] | None]] = [
    {
        "created_at": "2024-11-22T16:11:28Z",
        "description": None,
        "full_name": "astral-sh/.github",
        "html_url": "https://github.com/astral-sh/.github",
        "license": None,
        "name": ".github",
        "pushed_at": "2024-11-22T16:11:29Z",
        "releases_url": "https://api.github.com/repos/astral-sh/.github{/id}",
    },
    {
        "created_at": "2024-12-21T00:23:11Z",
        "description": None,
        "full_name": "astral-sh/archive-in-git-test",
        "html_url": "https://github.com/astral-sh/archive-in-git-test",
        "license": {"spdx_id": "MIT"},
        "name": "archive-in-git-test",
        "pushed_at": "2024-12-21T18:06:00Z",
        "releases_url": "https://api.github.com/repos/astral-sh/archive-in-git-test{/id}",
    },
    {
        "created_at": "2024-07-15T20:06:53Z",
        "description": None,
        "full_name": "astral-sh/docs",
        "html_url": "https://github.com/astral-sh/docs",
        "license": {"spdx_id": "Apache-2.0"},
        "name": "docs",
        "pushed_at": "2025-03-31T13:25:22Z",
        "releases_url": "https://api.github.com/repos/astral-sh/docs{/id}",
    },
    {
        "created_at": "2024-04-29T18:03:46Z",
        "description": "Types for communicating with a language server",
        "full_name": "astral-sh/lsp-types",
        "html_url": "https://github.com/astral-sh/lsp-types",
        "license": {"spdx_id": "MIT"},
        "name": "lsp-types",
        "pushed_at": "2024-04-29T18:13:15Z",
        "releases_url": "https://api.github.com/repos/astral-sh/lsp-types{/id}",
    },
    {
        "created_at": "2025-03-10T09:52:25Z",
        "description": "Run mypy and pyright over millions of lines of code",
        "full_name": "astral-sh/mypy_primer",
        "html_url": "https://github.com/astral-sh/mypy_primer",
        "license": {"spdx_id": "MIT"},
        "name": "mypy_primer",
        "pushed_at": "2025-03-28T13:11:42Z",
        "releases_url": "https://api.github.com/repos/astral-sh/mypy_primer{/id}",
    },
    {
        "created_at": "2024-08-02T02:19:38Z",
        "description": "A PyPI cache using nginx",
        "full_name": "astral-sh/nginx_pypi_cache",
        "html_url": "https://github.com/astral-sh/nginx_pypi_cache",
        "license": {"spdx_id": "MIT"},
        "name": "nginx_pypi_cache",
        "pushed_at": "2024-08-02T02:28:50Z",
        "releases_url": "https://api.github.com/repos/astral-sh/nginx_pypi_cache{/id}",
    },
    {
        "created_at": "2023-12-13T00:08:43Z",
        "description": "Python packaging scenarios",
        "full_name": "astral-sh/packse",
        "html_url": "https://github.com/astral-sh/packse",
        "license": {"spdx_id": "Apache-2.0"},
        "name": "packse",
        "open_issues": 9,
        "pushed_at": "2025-03-27T20:11:10Z",
        "releases_url": "https://api.github.com/repos/astral-sh/packse{/id}",
        "stargazers_count": 115,
    },
    {
        "created_at": "2023-11-08T22:48:02Z",
        "description": "PubGrub version solving algorithm implemented in Rust",
        "full_name": "astral-sh/pubgrub",
        "html_url": "https://github.com/astral-sh/pubgrub",
        "license": {"spdx_id": "MPL-2.0"},
        "name": "pubgrub",
        "open_issues": 2,
        "pushed_at": "2025-03-17T10:15:11Z",
        "releases_url": "https://api.github.com/repos/astral-sh/pubgrub{/id}",
    },
    {
        "created_at": "2024-03-14T18:00:52Z",
        "description": "A reverse proxy for testing Python package indexes",
        "full_name": "astral-sh/pypi-proxy",
        "html_url": "https://github.com/astral-sh/pypi-proxy",
        "license": None,
        "name": "pypi-proxy",
        "open_issues": 2,
        "pushed_at": "2025-01-29T22:12:27Z",
        "releases_url": "https://api.github.com/repos/astral-sh/pypi-proxy{/id}",
    },
    {
        "created_at": "2018-12-18T19:10:32Z",
        "description": "Produce redistributable builds of Python",
        "full_name": "astral-sh/python-build-standalone",
        "html_url": "https://github.com/astral-sh/python-build-standalone",
        "license": {"spdx_id": "MPL-2.0"},
        "name": "python-build-standalone",
        "open_issues": 110,
        "pushed_at": "2025-03-20T22:27:56Z",
        "releases_url": "https://api.github.com/repos/astral-sh/python-build-standalone{/id}",
        "stargazers_count": 2834,
    },
    {
        "created_at": "2024-07-02T16:45:21Z",
        "description": "Wrapper around reqwest to allow for client middleware chains.",
        "full_name": "astral-sh/reqwest-middleware",
        "html_url": "https://github.com/astral-sh/reqwest-middleware",
        "license": {"spdx_id": "Apache-2.0"},
        "name": "reqwest-middleware",
        "pushed_at": "2024-11-08T15:01:49Z",
        "releases_url": "https://api.github.com/repos/astral-sh/reqwest-middleware{/id}",
    },
    {
        "created_at": "2022-08-09T17:17:44Z",
        "description": "An extremely fast Python linter and code formatter, written in Rust.",
        "full_name": "astral-sh/ruff",
        "html_url": "https://github.com/astral-sh/ruff",
        "license": {"spdx_id": "MIT"},
        "name": "ruff",
        "open_issues": 1484,
        "pushed_at": "2025-04-01T17:47:13Z",
        "releases_url": "https://api.github.com/repos/astral-sh/ruff{/id}",
        "stargazers_count": 37413,
    },
    {
        "created_at": "2024-09-29T23:07:34Z",
        "description": "A GitHub Action to run Ruff",
        "full_name": "astral-sh/ruff-action",
        "html_url": "https://github.com/astral-sh/ruff-action",
        "license": {"spdx_id": "Apache-2.0"},
        "name": "ruff-action",
        "open_issues": 5,
        "pushed_at": "2025-03-27T04:53:31Z",
        "releases_url": "https://api.github.com/repos/astral-sh/ruff-action{/id}",
        "stargazers_count": 117,
    },
    {
        "created_at": "2024-12-31T15:06:53Z",
        "description": "An extremely fast Python linter and code formatter, written in Rust.",
        "full_name": "astral-sh/ruff-issue-template-test",
        "html_url": "https://github.com/astral-sh/ruff-issue-template-test",
        "license": {"spdx_id": "MIT"},
        "name": "ruff-issue-template-test",
        "pushed_at": "2024-12-31T15:08:12Z",
        "releases_url": "https://api.github.com/repos/astral-sh/ruff-issue-template-test{/id}",
    },
    {
        "created_at": "2022-12-17T21:51:38Z",
        "description": "A Language Server Protocol implementation for Ruff.",
        "full_name": "astral-sh/ruff-lsp",
        "html_url": "https://github.com/astral-sh/ruff-lsp",
        "license": {"spdx_id": "NOASSERTION"},
        "name": "ruff-lsp",
        "open_issues": 30,
        "pushed_at": "2025-02-10T13:17:59Z",
        "releases_url": "https://api.github.com/repos/astral-sh/ruff-lsp{/id}",
        "stargazers_count": 1426,
    },
    {
        "created_at": "2022-09-20T02:52:35Z",
        "description": "A pre-commit hook for Ruff.",
        "full_name": "astral-sh/ruff-pre-commit",
        "html_url": "https://github.com/astral-sh/ruff-pre-commit",
        "license": {"spdx_id": "Apache-2.0"},
        "name": "ruff-pre-commit",
        "open_issues": 20,
        "pushed_at": "2025-03-21T13:36:57Z",
        "releases_url": "https://api.github.com/repos/astral-sh/ruff-pre-commit{/id}",
        "stargazers_count": 1207,
    },
    {
        "created_at": "2022-11-08T03:42:36Z",
        "description": "A Visual Studio Code extension with support for the Ruff linter.",
        "full_name": "astral-sh/ruff-vscode",
        "html_url": "https://github.com/astral-sh/ruff-vscode",
        "license": {"spdx_id": "NOASSERTION"},
        "name": "ruff-vscode",
        "open_issues": 59,
        "pushed_at": "2025-03-21T14:37:17Z",
        "releases_url": "https://api.github.com/repos/astral-sh/ruff-vscode{/id}",
        "stargazers_count": 1316,
    },
    {
        "created_at": "2022-08-18T01:14:19Z",
        "description": "A Python Interpreter written in Rust",
        "full_name": "astral-sh/RustPython",
        "html_url": "https://github.com/astral-sh/RustPython",
        "license": {"spdx_id": "MIT"},
        "name": "RustPython",
        "pushed_at": "2023-04-26T21:06:56Z",
        "releases_url": "https://api.github.com/repos/astral-sh/RustPython{/id}",
    },
    {
        "created_at": "2023-05-11T09:23:46Z",
        "description": None,
        "full_name": "astral-sh/RustPython-Parser",
        "html_url": "https://github.com/astral-sh/RustPython-Parser",
        "license": {"spdx_id": "MIT"},
        "name": "RustPython-Parser",
        "open_issues": 1,
        "pushed_at": "2023-07-26T22:53:35Z",
        "releases_url": "https://api.github.com/repos/astral-sh/RustPython-Parser{/id}",
    },
    {
        "created_at": "2023-04-22T22:23:54Z",
        "description": "a Hassle-Free Python Experience",
        "full_name": "astral-sh/rye",
        "html_url": "https://github.com/astral-sh/rye",
        "license": {"spdx_id": "MIT"},
        "name": "rye",
        "open_issues": 332,
        "pushed_at": "2025-03-31T00:28:22Z",
        "releases_url": "https://api.github.com/repos/astral-sh/rye{/id}",
        "stargazers_count": 14108,
    },
    {
        "created_at": "2024-10-31T18:34:35Z",
        "description": None,
        "full_name": "astral-sh/sanitize-wheel-test",
        "html_url": "https://github.com/astral-sh/sanitize-wheel-test",
        "license": None,
        "name": "sanitize-wheel-test",
        "pushed_at": "2024-10-31T18:42:15Z",
        "releases_url": "https://api.github.com/repos/astral-sh/sanitize-wheel-test{/id}",
    },
    {
        "created_at": "2023-05-22T09:59:38Z",
        "description": "A collection of JSON schema files including full API",
        "full_name": "astral-sh/schemastore",
        "html_url": "https://github.com/astral-sh/schemastore",
        "license": {"spdx_id": "Apache-2.0"},
        "name": "schemastore",
        "pushed_at": "2025-03-13T18:45:56Z",
        "releases_url": "https://api.github.com/repos/astral-sh/schemastore{/id}",
    },
    {
        "created_at": "2024-08-23T20:54:38Z",
        "description": "Set up your GitHub Actions workflow with a specific version of https://docs.astral.sh/uv/",
        "full_name": "astral-sh/setup-uv",
        "html_url": "https://github.com/astral-sh/setup-uv",
        "license": {"spdx_id": "MIT"},
        "name": "setup-uv",
        "open_issues": 22,
        "pushed_at": "2025-04-01T10:30:02Z",
        "releases_url": "https://api.github.com/repos/astral-sh/setup-uv{/id}",
        "stargazers_count": 348,
    },
    {
        "created_at": "2024-08-14T16:58:46Z",
        "description": "Fast, zero-copy HTML Parser written in Rust",
        "full_name": "astral-sh/tl",
        "html_url": "https://github.com/astral-sh/tl",
        "license": {"spdx_id": "MIT"},
        "name": "tl",
        "pushed_at": "2024-08-25T23:55:46Z",
        "releases_url": "https://api.github.com/repos/astral-sh/tl{/id}",
    },
    {
        "created_at": "2024-12-09T01:55:07Z",
        "description": " A tar archive reading/writing library for async Rust. ",
        "full_name": "astral-sh/tokio-tar",
        "html_url": "https://github.com/astral-sh/tokio-tar",
        "license": {"spdx_id": "Apache-2.0"},
        "name": "tokio-tar",
        "open_issues": 2,
        "pushed_at": "2025-03-18T02:24:44Z",
        "releases_url": "https://api.github.com/repos/astral-sh/tokio-tar{/id}",
        "stargazers_count": 11,
    },
    {
        "created_at": "2023-07-24T08:19:39Z",
        "description": "black formatted for our CI checks",
        "full_name": "astral-sh/transformers",
        "html_url": "https://github.com/astral-sh/transformers",
        "license": {"spdx_id": "Apache-2.0"},
        "name": "transformers",
        "pushed_at": "2023-07-24T07:51:16Z",
        "releases_url": "https://api.github.com/repos/astral-sh/transformers{/id}",
    },
    {
        "created_at": "2024-10-28T20:14:28Z",
        "description": "A complete, self-contained example for trusted publishing with uv ",
        "full_name": "astral-sh/trusted-publishing-examples",
        "html_url": "https://github.com/astral-sh/trusted-publishing-examples",
        "license": None,
        "name": "trusted-publishing-examples",
        "open_issues": 1,
        "pushed_at": "2024-10-28T20:20:13Z",
        "releases_url": "https://api.github.com/repos/astral-sh/trusted-publishing-examples{/id}",
    },
    {
        "created_at": "2023-10-02T20:24:11Z",
        "description": "An extremely fast Python package and project manager, written in Rust.",
        "full_name": "astral-sh/uv",
        "html_url": "https://github.com/astral-sh/uv",
        "license": {"spdx_id": "Apache-2.0"},
        "name": "uv",
        "open_issues": 1568,
        "pushed_at": "2025-04-01T17:09:06Z",
        "releases_url": "https://api.github.com/repos/astral-sh/uv{/id}",
        "stargazers_count": 47487,
    },
    {
        "created_at": "2025-01-02T18:03:47Z",
        "description": "An example of using uv with AWS Lambda",
        "full_name": "astral-sh/uv-aws-lambda-example",
        "html_url": "https://github.com/astral-sh/uv-aws-lambda-example",
        "license": {"spdx_id": "MIT"},
        "name": "uv-aws-lambda-example",
        "open_issues": 1,
        "pushed_at": "2025-01-08T21:57:41Z",
        "releases_url": "https://api.github.com/repos/astral-sh/uv-aws-lambda-example{/id}",
    },
    {
        "created_at": "2024-12-03T04:53:35Z",
        "description": None,
        "full_name": "astral-sh/uv-backwards-path-test",
        "html_url": "https://github.com/astral-sh/uv-backwards-path-test",
        "license": {"spdx_id": "MIT"},
        "name": "uv-backwards-path-test",
        "pushed_at": "2024-12-03T04:58:16Z",
        "releases_url": "https://api.github.com/repos/astral-sh/uv-backwards-path-test{/id}",
    },
]
