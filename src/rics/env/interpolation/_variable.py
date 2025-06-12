import re
from dataclasses import dataclass
from os import environ
from typing import ClassVar


@dataclass(frozen=True)
class Variable:
    """Representation of an environment variable."""

    PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"\${[ \t]*(\w+)[ \t]*(?::(.*))?}?}")
    """The Regex pattern used to find variables in strings."""

    name: str
    """Name of the environment variable, e.g. ``PATH`` or ``USER``."""
    default: str | None
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
    def parse_string(cls, s: str) -> list["Variable"]:  # noqa: PLR0912
        """Extract a list of ``Variable``-instances from a string `s`."""
        retval = []
        prev_is_dollar_sign: bool = False
        n_open: int = 0

        state = "search"

        full_match: list[str] = []
        default: list[str] = []
        name: list[str] = []

        def make(*, make_default: bool) -> None:
            nonlocal state

            var = Variable(
                "".join(name).strip(),
                default="".join(default) if make_default else None,
                full_match="".join(full_match),
            )
            name.clear()
            default.clear()
            full_match.clear()
            state = "search"
            retval.append(var)

        for c in s:
            if state != "search":
                full_match.append(c)

            if c == "{":
                n_open += 1
            elif c == "}":
                n_open -= 1

            if state == "search":
                if prev_is_dollar_sign and c == "{":
                    full_match.append("${")
                    state = "name"
            elif state == "name":
                if c == "}":
                    make(make_default=False)
                elif c == ":":
                    state = "default"
                else:
                    name.append(c)
            elif state == "default":
                if n_open == 0:
                    make(make_default=True)
                else:
                    default.append(c)

            prev_is_dollar_sign = c == "$"

        return [var for var in retval if var.name.isidentifier()]

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
                    raise NotImplementedError("inner match must be stripped")

                return inner.get_value(resolve_nested_defaults=resolve_nested_defaults)

            elif len(inners) > 1:
                raise NotImplementedError(f"Multiple inner variables not supported. Got: {inners} from {self}")

        return self.default


class UnsetVariableError(ValueError):
    """Error message for unset variables."""

    def __init__(self, name: str, message: str = "Not set.") -> None:
        super().__init__(f"Required Environment Variable {name!r}: {message}")
        self.name = name
