from pathlib import Path

import pytest

# shortcut: private pytest API; there is no public way to list a module's fixtures.
from _pytest.fixtures import FixtureFunctionDefinition

from rics import _pytest_fixtures

RESOURCES = Path(__file__).parent / "resources/pytest_fixtures"
FIXTURES = [name for name, obj in vars(_pytest_fixtures).items() if isinstance(obj, FixtureFunctionDefinition)]
assert FIXTURES, "Fixture discovery is broken."


@pytest.mark.parametrize("name", FIXTURES)
def test_fixture(pytester, name):
    resource = RESOURCES / f"{name}.py"
    assert resource.is_file(), f"Fixture {name!r} has no test. Add {resource}."
    pytester.makepyfile(**{f"test_{name}": resource.read_text()})
    assert pytester.runpytest("-p", "rics._pytest_fixtures").ret == pytest.ExitCode.OK
