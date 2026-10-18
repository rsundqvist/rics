import functools

import pytest

from rics import misc

from .data import Foo


@pytest.mark.parametrize(
    "obj, name",
    [
        (dict, "dict"),
        (type({"a": 1}.keys()), "dict_keys"),
    ],
)
def test_builtin_not_reexported(obj, name):
    assert misc.get_public_module(obj, resolve_reexport=True) == "builtins"
    assert misc.get_public_module(obj, resolve_reexport=True, include_name=True) == "builtins." + name


def test_private_module_round_trip():
    from rics._internal_support.changelog import split_changelog

    name = misc.get_public_module(split_changelog, resolve_reexport=True, include_name=True)
    assert misc.get_by_full_name(name) is split_changelog


@pytest.mark.parametrize(
    "obj, expected",
    [
        (functools.partial(len), "functools"),
        (Foo(), "tests.test_misc.data"),
        # Only the public part of the module; `obj` isn't in `rics`.
        (type("Private", (), {"__module__": "rics._private"})(), "rics"),
    ],
)
def test_no_qualname(obj, expected):
    assert misc.get_public_module(obj, resolve_reexport=True, include_name=True) == expected


@pytest.mark.xfail(
    strict=True,
    reason="Accepted limitation; matching a private C module (`_operator`) to its public reexporter takes heuristics.",
)
def test_private_c_module():
    import operator

    assert misc.get_public_module(operator.add, resolve_reexport=True, include_name=True) == "operator.add"
    assert misc.tname(operator.add, include_module=True) == "operator.add"


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Unimportable modules raise; catch ImportError in get_public_module if a real case turns up. pybind11's"
        " internal `pybind11_builtins` is one, but tname no longer looks it up (see test_tname.py::test_pybind11)."
    ),
)
@pytest.mark.parametrize("module", ["no_such_module", "rics.no_such_module"])
class TestUnimportableModule:
    @pytest.fixture
    def ghost(self, module):
        return type("Ghost", (), {"__module__": module})

    def test_get_public_module(self, ghost, module):
        assert misc.get_public_module(ghost) == module
        assert misc.get_public_module(ghost, resolve_reexport=True) == module
        assert misc.get_public_module(ghost, resolve_reexport=True, include_name=True) == f"{module}.Ghost"

    def test_tname(self, ghost, module):
        assert misc.tname(ghost, include_module=True) == f"{module}.Ghost"
        assert misc.tname(ghost(), include_module=True) == f"{module}.Ghost"
