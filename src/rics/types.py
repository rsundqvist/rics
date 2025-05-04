"""Types used by this package."""

import os as _os
import typing as _t
from collections import abc as _abc
from enum import Enum as _Enum
from pathlib import Path as _Path

AnyPath: _t.TypeAlias = str | _os.PathLike[str] | _Path
"""Any path-like type; see :func:`~rics.paths.parse_any_path`."""

T = _t.TypeVar("T")
"""A type var with no type bounds."""
EnumT = _t.TypeVar("EnumT", bound=_Enum)
"""A type var bounded by :py:class:`enum.Enum`."""


def verify_enum(
    value: str | EnumT,
    enum_type: type[EnumT],
    *,
    name: str | None = None,
) -> EnumT:
    """Verify enum value.

    Args:
        value: User input value; either a ``str`` or an enum.
        enum_type: Desired enum type.
        name: Name of the user-facing argument. Used in error messages. Derive if ``None``.

    Returns:
        A enum of the given `enum_type`.

    Examples:
        Basic usage.

        >>> from enum import Enum, auto
        >>> class Response(Enum):
        ...     Yes = auto()
        ...     No = auto()

        Matching is case-insensitive when strings are given.

        >>> verify_enum("NO", Response)
        '<Response.No: 2>'

        Enums may also be passed.

        >>> verify_enum(Response.Yes, Response)
        '<Response.Yes: 1>'

        The default variable name used for errors is derived using :func:`rics.strings.camel_to_snake`.

        >>> verify_enum("x", Response)  # doctest: +SKIP
        TypeError: Bad response='x'; expected a Response enum option: Response.Yes | Response.No).

    Notes:
        This function wraps :meth:`LiteralHelper.from_enum`.
    """
    return LiteralHelper.from_enum(enum_type, default_name=name).check(value)


def verify_literal(
    value: _t.Any,
    literal_type: _abc.Collection[T] | type[T] | _t.Any,  # Runtime type is typically <typing special form>.
    *,
    name: str = "value",
    type_name: str | None = None,
    exc_type: type[Exception] | None = None,
    normalizer: _abc.Callable[[_t.Any], _t.Any] | None = None,
) -> T:
    """Verify enum value.

    Args:
        value: User input value; either a ``str`` or an enum.
        literal_type: A ``typing.Literal`` type alias or a collection of permitted values.
        name: Name of the user-facing argument. Used in error messages.
        type_name: Name of the type itself. Used in error messages.
        exc_type: Exception type to raise. Default is :py:class:`TypeError`.
        normalizer: A callable ``(value | option) -> new_value`` to use if `value` does not match exactly.

    Returns:
        A valid ``Literal`` value.

    Examples:
        Basic usage.

        >>> from typing import Literal
        >>> verify_literal("no", Literal["yes", "no"])
        'no'

        Note that the output type will be ``Any`` unless a collection is used (a named ``TypeAlias`` is not enough).
        This is due to a limitation in the Python typing machinery. To get around this, you need to use an explicitly
        typed output variable.

        >>> YesOrNot = Literal["yes", "no"]
        >>> yes_or_no: YesOrNot = verify_literal("Yes!", YesOrNot)  # doctest: +SKIP
        TypeError: Bad value='Yes!'; expected one of ('yes', 'no').

        By default, a :py:class:`TypeError` is raised if the input value does not match the literal type.

        .. hint::

           See the :class:`LiteralHelper` class docs for more examples.
    """
    return LiteralHelper[T](
        literal_type=literal_type,
        default_name=name,
        type_name=type_name,
        exc_type=exc_type,
        normalizer=normalizer,
    ).check(value)


class LiteralHelper(_t.Generic[T]):
    """Support class for :func:`verify_literal`.

    Using this class may improve performance when the same literal type is verified multiple times.

    Examples:
        Basic usage.

        >>> from typing import Literal
        >>> YesOrNo = Literal["yes", "no"]
        >>> helper = LiteralHelper[YesOrNo](YesOrNo, type_name="YesOrNo")

        The original value is returned as-is.

        >>> helper.check("yes")
        'yes'

        The helper class itself is callable.

        >>> helper("YES")  # doctest: +SKIP
        TypeError: Bad value='YES'; expected a YesOrNo['yes', 'no'].

        Pass an explicit `name` to customize the error message for a single check call.

        >>> helper("YES", name="user input")  # doctest: +SKIP
        TypeError: Bad user input='YES'; expected a YesOrNo['yes', 'no'].

        Using a normalizer.

        >>> normalizing_helper = LiteralHelper(YesOrNo, normalizer=str.lower)
        >>> normalizing_helper("YES")
        'yes'

        The normalizer is applied only if the original value doesn't match exactly.

    Notes:
        Explicitly typed helpers (e.g. ``LiteralHelper[YesOrNo](...)``) don't require typed output variables, even when
        using type aliases instead of collections. This is another advantage of using the helper instead of
        :func:`verify_literal`.
    """

    def __init__(
        self,
        literal_type: _abc.Collection[T] | type[T] | _t.Any,  # Runtime type is typically <typing special form>.
        *,
        default_name: str = "value",
        type_name: str | None = None,
        exc_type: type[BaseException] | None = None,
        normalizer: _abc.Callable[[_t.Any | T], _t.Any] | None = None,
    ) -> None:
        options = self._extract_options(literal_type)
        if not options:
            raise ValueError(f"Could not derive options from {literal_type!r}.")

        self._name = default_name
        self._type_name = type_name
        self._exc_type: type[BaseException] = TypeError if exc_type is None else exc_type
        self._options = options
        self._normalizer = normalizer

    @classmethod
    def from_enum(cls, enum_type: type[EnumT], *, default_name: str | None = None) -> "LiteralHelper[EnumT]":
        """Construct helper for an :class:`enum.Enum` type.

        Args:
            enum_type: Desired enum type.
            default_name: Default name of the user-facing argument. Used in error messages. Derive if ``None``.

        Returns:
            A ``LiteralHelper`` constructor.
        """
        if default_name is None:
            from rics.strings import camel_to_snake

            default_name = camel_to_snake(enum_type.__name__)

        return LiteralHelper(
            literal_type=enum_type,
            default_name=default_name,
            type_name=None,  # Derived and pretty-printed on failure if None.
            normalizer=cls._enum_normalizer,
        )

    @_t.overload
    def read_env(self, variable: str, *, default: T | None, split: str) -> list[T]: ...
    @_t.overload
    def read_env(self, variable: str, *, default: T | None, split: None = None) -> T: ...
    def read_env(self, variable: str, *, default: T | None, split: str | None = None) -> T | list[T]:
        """Read environment value.

        Args:
            variable: Environment variable name.
            default: Value to use is `variable` is not set or blank. Pass ``None`` to raise.
            split: Character to split on. Returns ``list[T]`` when set.

        Returns:
            A :attr:`T`, or a list thereof (if `split` is set).

        Notes:
            Use the :mod:`rics.env.read` functions to read primitive types such as booleans.
        """
        import os

        value = os.environ.get(variable, "").strip()
        if default is None:
            if variable not in os.environ:
                self._raise("<not set>", variable)
            elif not value:
                self._raise("<blank>", variable)
        elif not value:
            return default if split is None else [default]

        if split is None:
            return self.check(value, name=variable)

        values = value.split(split)
        return [self.check(value, name=f"{variable}[{i}]") for i, value in enumerate(map(str.strip, values)) if value]

    @classmethod
    def _enum_normalizer(cls, arg: _t.Any) -> str:
        return arg.name.lower() if isinstance(arg, _Enum) else str(arg).strip().lower()

    @property
    def options(self) -> tuple[T, ...]:
        """Permitted options as explicit values."""
        return self._options

    def check(self, value: _t.Any, name: str | None = None) -> T:
        """Alias of ``__call__``.

        Args:
            value: User input value.
            name: Name to use for this call.

        Returns:
            A valid value.
        """
        name = self._name if name is None else name
        options = self._options

        if value in options:
            return value  # type: ignore[no-any-return]

        normalizer = self._normalizer
        if normalizer:
            normalized_value = normalizer(value)
            for option in options:
                if normalizer(option) == normalized_value:
                    return option

        self._raise(repr(value), name)

    __call__ = check

    def _raise(self, value: str, name: str) -> _t.Never:
        options = self._options

        if self._type_name is None:
            if isinstance(options[0], _Enum):
                pretty_options = f"a {type(options[0]).__name__} enum option: {{ {' | '.join(map(str, options))} }}"
            else:
                pretty_options = f"one of {options}"
        else:
            pretty_options = f"a {self._type_name}[{', '.join(map(repr, options))}]"

        msg = f"Bad {name}={value}; expected {pretty_options}."
        raise self._exc_type(msg)

    @classmethod
    def _extract_options(cls, literal_type: _abc.Collection[T] | _t.Any) -> tuple[T, ...]:
        if isinstance(literal_type, type(_t.Literal[None])):
            return (*_t.get_args(literal_type),)

        if isinstance(literal_type, _abc.Collection) and not isinstance(literal_type, str):
            return (*literal_type,)

        union_type = type(_t.Union[str, int])  # noqa: UP007
        if isinstance(literal_type, union_type):
            from_union = cls._from_union(literal_type)
            if from_union:
                return from_union

        msg = f"Invalid type: {literal_type!r}. Expected a Literal, Union of Literal, Collection, or Enum."
        raise TypeError(msg)

    @classmethod
    def _from_union(cls, literal_type: _t.Any) -> tuple[T, ...]:
        literal_cls = type(_t.Literal[None])

        literals = []
        types = _t.get_args(literal_type)
        for t in types:
            if not isinstance(t, literal_cls):
                return ()
            for literal in _t.get_args(t):
                if literal not in literals:
                    literals.append(literal)

        return (*literals,)
