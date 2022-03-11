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


@pytest.mark.parametrize(
    "end, expected",
    [
        (0.00000001, "1e-08 sec"),
        (0.0000002, "2e-07 sec"),
        (0.000003, "3e-06 sec"),
        (0.00004, "4e-05 sec"),
        (0.0001, "0.0001 sec"),
        (0.001, "0.001 sec"),
        (0.753, "0.753 sec"),
        (1.0, "1.00 sec"),
        (1.5, "1.50 sec"),
        (21780, "6:03:00"),
        (21780.49, "6:03:00"),
        (21780.51, "6:03:01"),
    ],
)
def test_format_perf_counter(end, expected):
    assert misc.format_perf_counter(0, end) == expected


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
