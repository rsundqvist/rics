import os
import tempfile
from pathlib import Path

import pytest as pytest

from rics.utility import misc


def test_tname():
    class Bar:
        def hi(self):
            pass

    assert misc.tname(Bar()) == "Bar"
    assert misc.tname(Bar) == "Bar"
    assert misc.tname(Bar().hi) == "hi"  # fmt: off


def test_tname_callable_class():
    class Bar:
        def __call__(self):
            return None

    assert misc.tname(Bar) == "Bar"
    assert misc.tname(Bar()) == "Bar"


def test_get_local_or_remote():
    def my_postprocessor(p):
        return ["my-data", {"is": "amazing"}]

    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)

        with open(base_path.joinpath("foo.txt"), "w") as f:
            f.write("test")

        path = misc.get_local_or_remote("foo.txt", tmpdir, show_progress=False)
        assert path == base_path.joinpath("foo.txt")

        path = misc.get_local_or_remote("foo.txt", tmpdir, show_progress=False, postprocessor=my_postprocessor)
        assert path == base_path.joinpath("my_postprocessor/foo.pkl")
        with open(path, "rb") as f:
            import pickle

            assert ["my-data", {"is": "amazing"}] == pickle.load(f)


def test_read_env_or_literal():
    os.environ["TEST_ENV_VAR"] = "env-foo"

    assert misc.read_env_or_literal("foo") == "foo"
    assert misc.read_env_or_literal("@TEST_ENV_VAR") == "env-foo"

    with pytest.raises(KeyError):
        assert misc.read_env_or_literal("@foo")


def test_not_serializable():
    def foo():
        pass

    assert not misc.serializable(foo)
