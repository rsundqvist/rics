import pytest

from rics import misc


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
