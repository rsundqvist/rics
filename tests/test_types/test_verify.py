from enum import Enum
from typing import Literal, assert_type

import pytest

from rics.types import LiteralHelper, verify_enum, verify_literal

AorBLiteral = Literal["a", "b"]


class TestLiteral:
    def test_invalid(self):
        with pytest.raises(TypeError) as exc_info:
            verify_literal("x", AorBLiteral)

        assert str(exc_info.value) == "Bad value='x'; expected one of ('a', 'b')."

    def test_invalid_explicit_name(self):
        with pytest.raises(TypeError) as exc_info:
            verify_literal("x", AorBLiteral, type_name="MyLiteral")

        assert str(exc_info.value) == "Bad value='x'; expected a MyLiteral['a', 'b']."


class AOrB(Enum):
    a = 1
    b = 2


class TestEnum:
    def test_invalid(self):
        with pytest.raises(TypeError) as exc_info:
            verify_enum("x", AOrB)

        assert str(exc_info.value) == "Bad a_or_b='x'; expected a AOrB enum option: { AOrB.a | AOrB.b }."

    def test_type(self):
        actual = verify_enum("a", AOrB)
        assert_type(actual, AOrB)
        assert actual == AOrB.a

    def test_explicit_name(self):
        with pytest.raises(TypeError) as exc_info:
            verify_enum("x", AOrB, name="user enum input")

        assert str(exc_info.value) == "Bad user enum input='x'; expected a AOrB enum option: { AOrB.a | AOrB.b }."


class TestInvalidType:
    def test_unknown_type(self):
        with pytest.raises(TypeError) as exc_info:
            LiteralHelper("im a string!")

        expected = "Invalid type: 'im a string!'. Expected a Literal, Union of Literal, Collection, or Enum."
        assert str(exc_info.value) == expected

    def test_empty(self):
        with pytest.raises(ValueError) as exc_info:
            LiteralHelper([])

        assert str(exc_info.value) == "Could not derive options from []."


Single = Literal["a"]
Double = Literal["b", "c"]
UnionLiteral = Single | Double | Literal["b"]


class TestLiteralUnions:
    def test_deduplicate(self):
        actual = LiteralHelper(UnionLiteral)._options  # type: ignore[var-annotated]
        assert actual == ("a", "b", "c")
