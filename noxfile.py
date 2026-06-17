"""Nox sessions."""

import platform

import nox
from nox.sessions import Session

nox.options.default_venv_backend = "uv"
nox.options.sessions = ["tests", "mypy"]
python_versions = ["3.11", "3.12", "3.13", "3.14"]


def install(session: Session) -> None:
    """Install the project using uv.

    The ``uv`` backend exports ``UV_PROJECT_ENVIRONMENT``/``UV_PYTHON`` into the session, so ``uv`` targets the session
    venv without an explicit ``--python``/``--active``.
    """
    session.run_install("uv", "sync", "--all-extras")
    session.install(".")


@nox.session(python=python_versions)
def tests(session: Session) -> None:
    """Run the test suite."""
    install(session)
    try:
        session.run(
            "inv",
            "tests",
            env={
                "COVERAGE_FILE": f".coverage.{platform.system()}.{platform.python_version()}",
            },
        )
    finally:
        if session.interactive:
            session.notify("coverage")


@nox.session
def coverage(session: Session) -> None:
    """Produce the coverage report."""
    install(session)
    args = session.posargs if session.posargs and len(session._runner.manifest) == 1 else []
    session.run("inv", "coverage", *args)


@nox.session(python=python_versions)
def mypy(session: Session) -> None:
    """Type-check using mypy."""
    install(session)
    session.run("inv", "mypy")


@nox.session(python="3.11")
def audit(session: Session) -> None:
    """Audit dependencies for known vulnerabilities."""
    install(session)
    session.run("inv", "audit")
