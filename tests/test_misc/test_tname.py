import pytest

from rics import misc

from .data import Foo, say_hi


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

    @pytest.mark.parametrize("n_wraps", [1, 2, 4])
    def test_wrapped(self, obj, expected, n_wraps):
        class Wrapper:
            def __init__(self, func):
                self.func = func

        for _ in range(n_wraps):
            obj = Wrapper(obj)
        assert misc.tname(obj, prefix_classname=True) == expected
