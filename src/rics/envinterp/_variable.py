from __future__ import annotations

import re
from dataclasses import dataclass
from os import environ
from typing import ClassVar, List, Optional


@dataclass(frozen=True)
class Variable:
    """Representation of an environment variable."""

    PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"\${(?:[ \t]*(\w+)[ \t]*)(?::(.*))?}?}")
    """The Regex pattern used to find variables in strings."""

    name: str
    """Name of the environment variable, e.g. ``PATH`` or ``USER``."""
    default: Optional[str]
    """Fallback value is the variable is unset."""
    full_match: str
    """The entire matching (sub)string as it were found in the input."""

    @classmethod
    def parse_first(cls, s: str) -> "Variable":
        """Return the first ``Variable`` found in `s`."""
        res = cls.parse_string(s)
        if not res:
            raise ValueError(f"No variables found in '{s}'")  # pragma: no cover
        return res[0]

    @classmethod
    def parse_string(cls, s: str) -> List["Variable"]:
        """Extract a list of ``Variable``-instances from a string `s`."""

        def parse_match(match: re.Match[str]) -> Variable:
            return Variable(
                name=match.group(1).strip(),
                default=match.group(2),
                full_match=match.group(0),
            )

        return list(map(parse_match, cls.PATTERN.finditer(s)))

    @property
    def is_required(self) -> bool:
        """Variables declared with only a name are required."""
        return self.default is None

    @property
    def is_optional(self) -> bool:
        """Variables declared with a default value are optional."""
        return not self.is_required

    def get_value(self, resolve_nested_defaults: bool = False) -> str:
        """Return the value of this ``Variable``.

        Args:
            resolve_nested_defaults: If ``True``, look for nested variables within this variable's `argument`-value
                if :attr:`name` is not set.

        Returns:
            The value of :attr:`name` in the system environment, or the specified default value.

        Raises:
            UnsetVariableError: If unset with no default specified. May also be raised by inner variables.
            NotImplementedError: If an inner ``Variable``, resolved from :attr:`default`, contains text that was not
                interpolated text.
            NotImplementedError: If :attr:`default` contains multiple inner variables.
        """
        if self.name in environ:
            return environ[self.name]

        if self.default is None:
            raise UnsetVariableError(self.name)

        if resolve_nested_defaults:
            stripped = self.default.strip()
            inners = Variable.parse_string(stripped)
            if len(inners) == 1:
                inner = inners[0]
                if inner.full_match != stripped:
                    raise NotImplementedError()

                return inner.get_value(resolve_nested_defaults=resolve_nested_defaults)

            elif len(inners) > 1:
                raise NotImplementedError(f"Multiple inner variables not supported. Got: {inners} from {self}")

        return self.default


class UnsetVariableError(ValueError):
    """Error message for unset variables."""

    def __init__(self, name: str, message: str = "Not set.") -> None:
        super().__init__(f"Required Environment Variable {name!r}: {message}")
        self.name = name
