import re
from dataclasses import dataclass
from typing import Iterable, List, Tuple, Union

from rics.translation.offline.types import PlaceholdersTuple
from rics.utility.misc import tname

FormatType = Union[str, "Format"]

_REQUIRED_ELEMENT_RE = r"{(?P<required>\w+)}"
_OPTIONAL_ELEMENT_REGEX = r"(?P<optional>\[(?P<left>.*?){(?P<optional_name>\w+)}(?P<right>.*?)\])"


class Format:
    """Format specification for translations strings.

    Translator formats are similar to regular f-strings, with two important exceptions:
    1. Positional arguments may not be used; ``'{}'`` is not accepted, correct form is ``'{key-name}'``.
    2. Substrings surrounded by ``[]`` denote an optional element.

    Args:
        fmt: A translation fstring.
    """

    PLACEHOLDER_PATTERN: re.Pattern = re.compile(_OPTIONAL_ELEMENT_REGEX + "|" + _REQUIRED_ELEMENT_RE)

    def __init__(self, fmt: str) -> None:
        self._fmt = fmt
        self._elements = self._parse_format_string(fmt)
        self._named_elements: List[NamedElement] = []
        for elem in self._elements:
            if isinstance(elem, NamedElement):
                self._named_elements.append(elem)

    def fstring(self, placeholders: Iterable[str] = None, positional: bool = False) -> str:
        """Create a format string for the given placeholders.

        Args:
            placeholders: Keys to keep. Passing None is equivalent to passing :attr:`required_placeholders`.
            positional: If True, remove names to return a positional fstring.

        Returns:
            An fstring with optional elements removed unless included in `placeholders`.

        Raises:
            KeyError: If required placeholders are missing.

        See Also:
            :attr:`required_placeholders`
        """
        placeholders = placeholders or self.required_placeholders
        missing_required_placeholders = set(self.required_placeholders).difference(placeholders)
        if missing_required_placeholders:
            raise KeyError(f"Required key(s) {missing_required_placeholders} missing from {placeholders=}.")

        return self._make_fstring(placeholders, positional=positional)

    def _make_fstring(self, placeholders: Iterable[str], positional: bool) -> str:
        parts = []
        for element in self._elements:
            if isinstance(element, NamedElement):
                if element.name in placeholders:
                    parts.append(element.positional_part if positional else element.part)
            else:
                parts.append(element.part)
        return "".join(parts)

    @staticmethod
    def parse(fmt: FormatType) -> "Format":
        """Parse a format.

        Args:
            fmt: Input to parse.

        Returns:
            A ``Format`` instance.
        """
        return fmt if isinstance(fmt, Format) else Format(fmt)

    @property
    def placeholders(self) -> PlaceholdersTuple:
        """All placeholders in the order in which they appear."""
        return tuple(e.name for e in self._named_elements)

    @property
    def required_placeholders(self) -> PlaceholdersTuple:
        """All required placeholders in the order in which they appear."""
        return tuple(e.name for e in filter(lambda e: e.required, self._named_elements))

    @property
    def optional_placeholders(self) -> PlaceholdersTuple:
        """All optional placeholders in the order in which they appear."""
        return tuple(e.name for e in filter(lambda e: not e.required, self._named_elements))

    @classmethod
    def _parse_format_string(cls, format_string: str) -> Tuple["Element", ...]:
        """Parse a translation format string.

        Args:
            format_string: A format string to parse.

        Returns:
            A tuple of elements.
        """
        ans = []
        pos = 0
        while True:
            match = Format.PLACEHOLDER_PATTERN.search(format_string, pos=pos)
            if match is None:
                break
            else:
                if match.start() > pos:
                    ans.append(Element(format_string[pos : match.start()], True))
                ans.append(from_match(match))
                pos = match.end()

        if pos < len(format_string):
            ans.append(Element(format_string[pos:], True))
        return tuple(ans)

    def __repr__(self) -> str:
        return f"{tname(self)}{tuple(e.part for e in self._elements)}"


_POSITIONAL_PATTERN: re.Pattern = re.compile(_REQUIRED_ELEMENT_RE)


@dataclass(frozen=True)
class Element:
    """A single translation element."""

    part: str
    required: bool

    @property
    def positional_part(self) -> str:
        """Return a positional copy of `part`."""
        return _POSITIONAL_PATTERN.sub("{}", self.part, 1)


@dataclass(frozen=True)
class NamedElement(Element):
    """A single translation element."""

    name: str


def from_match(match: re.Match) -> NamedElement:
    """Initialize an element from a RegEx match instance.

    Args:
        match: RegEx match instance.

    Returns:
        A new element.
    """
    part, required, key = (
        (
            match.group(0),
            True,
            match.group("required"),
        )
        if match.group("optional") is None
        else (  # fmt: off
            match.group("left") + "{" + match.group("optional_name") + "}" + match.group("right"),
            False,
            match.group("optional_name"),
        )
    )
    return NamedElement(part, required, key)
