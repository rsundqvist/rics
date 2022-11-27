import os

import pytest as pytest

from rics import misc


class Foo:
    @classmethod
    def bar(cls) -> str:
        return "a string"

    def __call__(self):
        return None

    def hi(self):
        pass


def plain_function():
    pass


def test_get_by_full_name():
    assert Foo == misc.get_by_full_name("tests.test_misc.Foo")

    with pytest.raises(ModuleNotFoundError):
        assert misc.get_by_full_name("tests.test_misc.Foo.bar")


def test_tname():
    assert misc.tname(None) == "None"
    assert misc.tname(Foo()) == "Foo"
    assert misc.tname(Foo) == "Foo"
    assert misc.tname(Foo().hi) == "hi"
    assert misc.tname(plain_function) == "plain_function"


def test_tname_callable_class():
    assert misc.tname(Foo) == "Foo"
    assert misc.tname(Foo()) == "Foo"


def test_instance_method_with_classname():
    print(f"{dir(Foo.hi)=}")
    assert misc.tname(Foo.hi, prefix_classname=True) == "Foo.hi"
    assert misc.tname(Foo.hi, prefix_classname=False) == "hi"


def test_class_method_with_classname():
    print(f"{dir(Foo.bar)=}")
    assert misc.tname(Foo.bar, prefix_classname=True) == "Foo.bar"
    assert misc.tname(Foo.bar, prefix_classname=False) == "bar"


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


def test_read_env_or_literal():
    os.environ["TEST_ENV_VAR"] = "env-foo"

    assert misc.read_env_or_literal("foo") == "foo"
    assert misc.read_env_or_literal("@TEST_ENV_VAR") == "env-foo"

    with pytest.raises(KeyError):
        assert misc.read_env_or_literal("@foo")


def test_serializable():
    def foo():
        pass

    assert not misc.serializable(foo)
    assert misc.serializable(misc.serializable)
