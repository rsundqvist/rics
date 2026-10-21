import functools
import math

import pandas as pd
import pytest

from rics import misc

from .data import ChildFoo, Foo, say_hi


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
        (say_hi, "say_hi"),
        (Foo.Bar, "Foo.Bar"),
        (Foo.Bar(), "Foo.Bar"),
        (Foo.Bar.inner_bar, "Foo.Bar.inner_bar"),
        (Foo.Bar().inner_bar, "Foo.Bar.inner_bar"),
        (Foo().Bar.inner_bar, "Foo.Bar.inner_bar"),
        (Foo().Bar().inner_bar, "Foo.Bar.inner_bar"),
    ],
)
class Test:
    def test_without_class(self, obj, expected):
        expected = expected.split(".")[-1]
        assert misc.tname(obj, prefix_classname=False) == expected
        assert misc.tname(obj) == expected

    def test_with_class(self, obj, expected):
        assert misc.tname(obj, prefix_classname=True) == expected

    def test_include_module(self, obj, expected):
        actual = misc.tname(obj, include_module=True, prefix_classname=True)
        if obj is None:
            assert actual == expected
            return
        if isinstance(obj, str):
            assert actual == "builtins.str"
            return

        assert actual == "tests.test_misc.data." + expected

    @pytest.mark.parametrize(
        "path",
        [
            "func",
            "func.func",
            "func.func.func.func",
            "inner",
            "wrapped.func",
            "func.inner.wrapped.func",
            # Levels with several matching attrs; the one listed first in `attrs` must win.
            "inner+wrapped",
            "wrapped.inner+func",
            "inner+wrapped+func.func.wrapped+inner",
        ],
    )
    def test_wrapped(self, obj, expected, path):
        attrs = ["func", "wrapped", "inner"]

        class Wrapper:
            def __init__(self, **kwargs):
                for attr, value in kwargs.items():
                    setattr(self, attr, value)

        def decoy(): ...

        for level in reversed(path.split(".")):
            names = level.split("+")
            winner = min(names, key=attrs.index)
            obj = Wrapper(**{name: obj if name == winner else decoy for name in names})

        assert misc.tname(obj, prefix_classname=True, attrs=attrs) == expected


@pytest.mark.parametrize(
    "include_module, expected",
    [
        (True, "rics.misc.format_kwargs"),
        (False, "format_kwargs"),
    ],
)
def test_attr_functools(include_module, expected):
    obj = misc.format_kwargs
    assert misc.tname(obj, include_module=include_module) == expected

    wrapped = functools.partial(obj)
    assert misc.tname(wrapped, include_module=include_module) == expected


def test_self_wrapping():
    class Wrapper:
        def __init__(self) -> None:
            self.func = self

    assert misc.tname(Wrapper()) == "Wrapper"


def test_self_wrapping_tries_remaining_attrs():
    class Wrapper:
        def __init__(self) -> None:
            self.func = self
            self.wrapped = len

    assert misc.tname(Wrapper(), attrs=["func", "wrapped"]) == "len"


def test_wrapper_cycle():
    class Wrapper:
        func: "Wrapper"

    a, b = Wrapper(), Wrapper()
    a.func, b.func = b, a

    with pytest.raises(RecursionError):
        misc.tname(a)


def test_empty_attrs_iterator():
    assert misc.tname(say_hi, attrs=iter([])) == "say_hi"


@pytest.mark.xfail(strict=True, reason="Accepted limitation; see the shortcut note in rics.misc._unwrap.")
@pytest.mark.parametrize("label", ["func", "fget"])
def test_attr_pandas(label):
    series = pd.Series([1], index=[label])

    assert misc.tname(series) == "Series"
    assert misc.tname(series, prefix_classname=True) == "Series"
    assert misc.tname(series, include_module=True) == "pandas.Series"


@pytest.mark.parametrize(
    "obj, expected",
    [
        (len, "builtins.len"),
        (functools.partial(print), "builtins.print"),
        (math.floor, "math.floor"),
        ([].append, "builtins.append"),
    ],
)
def test_builtin_include_module(obj, expected):
    assert misc.tname(obj, include_module=True) == expected


@pytest.mark.parametrize(
    "obj, expected",
    [
        (len, "builtin_function_or_method.len"),
        (math.floor, "builtin_function_or_method.floor"),
        ([].append, "builtin_function_or_method.append"),
    ],
)
def test_builtin_prefix_classname(obj, expected):
    # The type-name prefix is kept for 6.2.x: MultiCaseTimer derives candidate labels from it. See TODO in _get_name.
    assert misc.tname(obj, prefix_classname=True) == expected


def test_pybind11():
    # The `__self__` of a pybind11 function is an internal object whose type claims the unimportable 'pybind11_builtins'.
    path = pytest.importorskip("matplotlib._path")
    assert misc.tname(path.affine_transform, include_module=True) == "matplotlib.affine_transform"
    assert misc.tname(path.affine_transform, prefix_classname=True) == "builtin_function_or_method.affine_transform"


@pytest.mark.xfail(strict=True, reason="Accepted limitation; see the shortcut note in rics.misc._unwrap.")
def test_mock():
    from unittest.mock import Mock

    assert misc.tname(Mock(), include_module=True) == "unittest.mock.Mock"


@pytest.mark.parametrize(
    "obj, expected",
    [
        # Known limitation - can't get child through parent method
        (ChildFoo.a_property, "Foo.a_property"),
        (ChildFoo().a_property, "str"),
        (ChildFoo.hi, "Foo.hi"),  # No way to access the "real" parent from method
        (ChildFoo().hi, "ChildFoo.hi"),
        (ChildFoo.bar, "ChildFoo.bar"),
        (ChildFoo().bar, "ChildFoo.bar"),
    ],
)
def test_inheritance(obj, expected):
    assert misc.tname(obj, prefix_classname=True) == expected
