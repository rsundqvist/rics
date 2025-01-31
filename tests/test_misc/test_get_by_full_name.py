import pytest

from rics.misc import get_by_full_name

from .data import (
    MODULE,
    AbstractHello,
    Foo,
    HelloClassImpl,
    HiProtocol,
    hello_class_impl,
    hi_protocol_impl,
    my_foo,
)


@pytest.mark.parametrize("name", ["Foo", "tests.test_misc.data.Foo"])
def test_untyped(name):
    actual = get_by_full_name(name, default_module=MODULE)
    assert actual(1991).hi() == "Hi, 1991!"
    assert actual is Foo


class TestInstance:
    def test_plain(self):
        actual = get_by_full_name("my_foo", default_module=MODULE, instance_of=Foo)
        assert actual is my_foo

    def test_abstract(self):
        actual = get_by_full_name("hello_class_impl", default_module=MODULE, instance_of=AbstractHello)  # type: ignore[type-abstract]
        assert actual is hello_class_impl

    def test_protocol(self):
        actual = get_by_full_name("hi_protocol_impl", default_module=MODULE, instance_of=HiProtocol)  # type: ignore[type-abstract]
        assert actual is hi_protocol_impl

    def test_bad_plain(self):
        with pytest.raises(TypeError, match="instance of Foo"):
            get_by_full_name("hi_protocol_impl", default_module=MODULE, instance_of=Foo)

    def test_bad_abstract(self):
        with pytest.raises(TypeError, match="instance of AbstractHello"):
            get_by_full_name("my_foo", default_module=MODULE, instance_of=AbstractHello)  # type: ignore[type-abstract]

    def test_bad_protocol(self):
        with pytest.raises(TypeError, match="instance of HiProtocol"):
            get_by_full_name("hello_class_impl", default_module=MODULE, instance_of=HiProtocol)  # type: ignore[type-abstract]


class TestSubclass:
    @pytest.mark.parametrize("subclass_of", [Foo, HiProtocol])
    def test_foo_class(self, subclass_of):
        actual = get_by_full_name("Foo", default_module=MODULE, subclass_of=subclass_of)
        assert actual is Foo

    @pytest.mark.parametrize(
        "clazz, subclass_of",
        [
            (Foo, int),
            (Foo, AbstractHello),
            (HelloClassImpl, HiProtocol),
        ],
    )
    def test_does_not_inherit(self, clazz, subclass_of):
        with pytest.raises(TypeError, match="does not inherit"):
            get_by_full_name(clazz.__name__, default_module=MODULE, subclass_of=subclass_of)

        assert not isinstance(clazz(), subclass_of)

    @pytest.mark.parametrize(
        "name, subclass_of",
        [
            ("my_foo", Foo),
            ("say_hi", Foo),
        ],
    )
    def test_not_a_class(self, name, subclass_of):
        with pytest.raises(TypeError, match="not a class"):
            get_by_full_name(name, default_module=MODULE, subclass_of=subclass_of)


class TestLimitations:
    def test_dual_of_args(self):
        with pytest.raises(ValueError, match="least one of.*must be None"):
            get_by_full_name("my_foo", instance_of=int, subclass_of=int)  # type: ignore[call-overload]

    def test_parameterized_generics(self):
        with pytest.raises(TypeError, match="cannot be a parameterized generic"):
            get_by_full_name("my_foo", default_module=MODULE, instance_of=list[int])

        with pytest.raises(TypeError, match="cannot be a parameterized generic"):
            get_by_full_name("my_foo", default_module=MODULE, subclass_of=list[int])

    @pytest.mark.xfail(reason="Nested classes are not supported.")
    def test_nested(self):
        get_by_full_name("Foo.Bar", default_module=MODULE)

    def test_no_default(self):
        with pytest.raises(ValueError, match="fully qualified when no default module"):
            get_by_full_name("")
