from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

MODULE = __name__


class Foo:
    def __init__(self, n: int = 1):
        self.n = n

    class Bar:
        pass

    @classmethod
    def bar(cls) -> str:
        return "a string"

    def __call__(self):
        return None

    def hi(self) -> str:
        return f"Hi, {self.n}!"

    @property
    def a_property(self) -> str:
        return "property value"


my_foo = Foo(1999)


def say_hi():
    pass


class AbstractHello(ABC):
    @abstractmethod
    def hello(self) -> str:
        ...


class HelloClassImpl(AbstractHello):
    def hello(self) -> str:
        return "Hi!"


hello_class_impl = HelloClassImpl()


@runtime_checkable
class HiProtocol(Protocol):
    def hi(self) -> str:
        ...


class HiProtocolImpl(HiProtocol):
    def hi(self) -> str:
        return "Hi!"


hi_protocol_impl = HiProtocolImpl()
