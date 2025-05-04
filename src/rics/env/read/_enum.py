from typing import TYPE_CHECKING, overload

if TYPE_CHECKING:
    from rics.types import EnumT


@overload
def read_enum(var: str, default_or_type: "EnumT | type[EnumT]", *, split: str) -> list["EnumT"]: ...
@overload
def read_enum(var: str, default_or_type: "EnumT | type[EnumT]", *, split: None = None) -> "EnumT": ...
def read_enum(var: str, default_or_type: "EnumT | type[EnumT]", *, split: str | None = None) -> "EnumT | list[EnumT]":
    """Read ``enum`` variable.

    This function wraps :meth:`.LiteralHelper.from_enum` and :meth:`.LiteralHelper.read_env`.

    Args:
        var: Variable to read.
        default_or_type: Enum type or default enum value. Must be a concrete value (e.g. ``Animal.dog`` instead of just
            ``Animal``) to allow unset or blank `var` values.
        split: Character to split on. Returns ``list[EnumT]`` when set.

    Returns:
        An :attr:`~rics.types.EnumT` value, or a list thereof (if `split` is set).

    Raises:
        TypeError: If conversion fails.

    Examples:
        Basic usage.

        >>> from enum import Enum
        >>> class Animal(Enum):
        ...     cat = "meow"
        ...     dog = "woof"

        Enums are matched by name, never by value.

        >>> import os
        >>> os.environ["MY_ANIMAL"] = "cat"
        >>> read_enum("MY_ANIMAL", Animal)
        <Animal.cat: 'meow'>

        Input is always cleaned and normalized.

        >>> os.environ["MY_ANIMAL"] = " DOG"
        >>> read_enum("MY_ANIMAL", Animal)
        <Animal.dog: 'woof'>

        This also applies when reading multiple enums.

        >>> os.environ["MY_ANIMAL_LIST"] = " DOG, cat  , CAT"
        >>> read_enum("MY_ANIMAL_LIST", Animal, split=",")
        [<Animal.dog: 'woof'>, <Animal.cat: 'meow'>, <Animal.cat: 'meow'>]


        Unlike the other functions in this module, ``read_enum`` always runs in `strict` mode. Define a default for when
        the `var` is not set or blank by passing concrete value in the second position.

        >>> read_enum("MISSING_VARIABLE", Animal.dog)
        <Animal.dog: 'woof'>

        Unknown values will always raise.
    """
    from rics.types import LiteralHelper

    if isinstance(default_or_type, type):
        cls = default_or_type
        default = None
    else:
        cls = type(default_or_type)
        default = default_or_type

    return LiteralHelper.from_enum(cls).read_env(var, default=default, split=split)
