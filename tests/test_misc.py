import os

import pytest as pytest

from rics import misc
from rics.envinterp import UnsetVariableError


class Foo:
    @classmethod
    def bar(cls) -> str:
        return "a string"

    def __call__(self):
        return None

    def hi(self):
        pass

    @property
    def a_property(self) -> str:
        return "property value"


def plain_function():
    pass


def test_get_by_full_name():
    assert Foo == misc.get_by_full_name("tests.test_misc.Foo")

    with pytest.raises(ModuleNotFoundError):
        assert misc.get_by_full_name("tests.test_misc.Foo.bar")


def test_get_public_module():
    from rics.performance import MultiCaseTimer as obj

    assert misc.get_public_module(obj) == "rics.performance"
    assert misc.get_public_module(obj, resolve_reexport=True) == "rics.performance"
    assert misc.get_public_module(obj, resolve_reexport=True, include_name=True) == "rics.performance"


@pytest.mark.parametrize(
    "obj, expected",
    [
        (None, "None"),
        (Foo(), "Foo"),
        (Foo, "Foo"),
        (Foo.hi, "Foo.hi"),
        (Foo().hi, "Foo.hi"),
        (Foo.bar, "Foo.bar"),
        (Foo().bar, "Foo.bar"),
        (Foo.a_property, "Foo.a_property"),
        (Foo().a_property, "str"),
        (plain_function, "plain_function"),
    ],
)
class Test_tname:
    def test_without_class(self, obj, expected):
        expected = expected.split(".")[-1]
        assert misc.tname(obj, prefix_classname=False) == expected
        assert misc.tname(obj) == expected

    def test_with_class(self, obj, expected):
        assert misc.tname(obj, prefix_classname=True) == expected


def test_get_local_or_remote(tmp_path):
    def my_postprocessor(p):
        return ["my-data", {"is": "amazing"}]

    remote_root = "doesn't exist"

    with open(tmp_path.joinpath("foo.txt"), "w") as f:
        f.write("test")

    path = misc.get_local_or_remote("foo.txt", remote_root, tmp_path)
    assert path == tmp_path.joinpath("foo.txt")

    path = misc.get_local_or_remote("foo.txt", remote_root, tmp_path, postprocessor=my_postprocessor)
    assert path == tmp_path.joinpath("my_postprocessor/foo.pkl")

    with open(path, "rb") as f2:
        import pickle

        assert ["my-data", {"is": "amazing"}] == pickle.load(f2)


@pytest.mark.parametrize(
    "s, expected",
    [
        ("", ""),
        ("no vars!", "no vars!"),
        ("${ ENV_VAR0 \t} exists, but ${  ENV_VAR100  :not this} one", "VALUE0 exists, but not this one"),
    ],
)
def test_interpolate_environment_variables_default_args(s, expected):
    os.environ["ENV_VAR0"] = "VALUE0"
    os.environ["ENV_VAR1"] = "VALUE1"
    assert misc.interpolate_environment_variables(s) == expected


@pytest.mark.parametrize(
    "s, expected, kwargs",
    [
        ("${ENV_VAR0:${ENV_VAR0}}", ValueError, dict(allow_nested=False)),
        ("${HACKY}", "${NESTED}", dict(allow_nested=False)),
        ("${NOT_SET:}", UnsetVariableError, dict(allow_blank=False)),
        ("${BLANK}", "", dict(allow_blank=True)),
        ("${BLANK}", UnsetVariableError, dict(allow_blank=False)),
        ("${BLANK:${ BLANK }}", UnsetVariableError, dict()),
        ("${BLANK:${ NOT_SET }}", UnsetVariableError, dict()),
    ],
)
def test_interpolate_environment_variables(s, expected, kwargs):
    os.environ["ENV_VAR0"] = "VALUE0"
    os.environ["BLANK"] = " "
    os.environ["HACKY"] = "${NESTED}"

    try:
        actual = misc.interpolate_environment_variables(s, **kwargs)
    except (ValueError, UnsetVariableError, NotImplementedError) as e:
        actual = e  # type: ignore

    if isinstance(actual, str):
        assert actual == expected
        return

    assert isinstance(actual, expected)


def test_serializable():
    def foo():
        pass

    assert not misc.serializable(foo)
    assert misc.serializable(misc.serializable)
