import os
import sys
from pathlib import Path

import pytest

from rics.paths import any_path_to_path, any_path_to_str, parse_any_path

if os.getenv("CI") == "true" and os.name == "nt":
    pytest.skip("Windows paths are a mess in Actions.", allow_module_level=True)

paths = pytest.mark.parametrize("path", ["~/home.txt", Path("./relative.txt"), Path("/absolute/path.txt")])


@paths
def test_str(path):
    result = any_path_to_str(path)
    assert isinstance(result, str)
    assert result == str(path)


@paths
def test_pathlib(path):
    result = any_path_to_path(path)
    assert isinstance(result, Path)
    assert result == Path(str(path))


class TestPostprocessors:
    @paths
    def test_identity(self, path):
        actual = parse_any_path(path, cls=Path, postprocessor=lambda x: x)
        assert isinstance(actual, Path)
        assert actual == Path(str(path))

    @paths
    def test_none(self, path):
        actual = parse_any_path(path, cls=Path, postprocessor=lambda _: None)
        assert isinstance(actual, Path)
        assert actual == Path(str(path))

    @pytest.mark.parametrize(
        "path, expected",
        [
            ("./relative.txt", Path.cwd() / "relative.txt"),
            ("/absolute/path.txt", Path("/absolute/path.txt")),
        ],
    )
    def test_absolute(self, path, expected):
        actual = parse_any_path(path, cls=Path, postprocessor=Path.absolute)
        assert actual == expected

    def test_bad_type(self):
        with pytest.raises(TypeError, match="returned result=1 of type `int`"):
            any_path_to_path(
                "whatever",
                postprocessor=lambda _: 1,  # type: ignore[arg-type, return-value]
            )

    def test_bool(self):
        assert any_path_to_path(Path.home(), postprocessor=Path.is_dir) == Path.home()

        cls = "Path" if sys.version_info < (3, 13) else "PathBase"
        with pytest.raises(ValueError, match=f"{cls}.is_file"):
            any_path_to_path(Path.home(), postprocessor=Path.is_file)


class TestWonky:
    def test_strange_path_type(self):
        actual = any_path_to_path(1)  # type: ignore[arg-type]
        assert actual == Path("1")

    def test_strange_cls_type(self):
        actual = parse_any_path(1, cls=int)  # type: ignore[arg-type, type-var]
        assert actual == 1

    def test_last_resort_fails(self):
        with pytest.raises(TypeError, match="Cannot convert") as e:
            parse_any_path("this is no int!", cls=int)  # type: ignore[type-var]
        assert e.value.args[0] == "Cannot convert path='this is no int!' from type(path)=`str` to cls=`int`."
