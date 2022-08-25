"""Utility module for parsing raw ``Format`` input strings."""

from dataclasses import dataclass as _dataclass
from string import Formatter as _Formatter
from typing import List, List as _List

OPTIONAL_BLOCK_START_DELIMITER = "["
OPTIONAL_BLOCK_END_DELIMITER = "]"
OPTIONAL_BLOCK_DELIMITER_ESCAPED = "\\"

_formatter = _Formatter()
_hint = "Hint: Use '\\' to escape '[' and ']', e.g. '\\[', to use angle brackets as regular characters."


class MalformedOptionalBlockError(ValueError):
    """Error raised for improper optional blocks."""

    @staticmethod
    def get_marker_row(format_string: str, i: int = -1, open_position: int = -1) -> str:
        """Get a string of length equal to `format_string` which marks problem locations."""
        markers = [" "] * len(format_string)

        if i != -1:
            markers[i] = "^"
        if open_position != -1:
            markers[open_position] = "^"
        return "".join(markers)


class UnusedOptionalBlockError(MalformedOptionalBlockError):
    """Errors raised when optional blocks do not use any placeholders."""

    def __init__(self, format_string: str, i: int, open_position: int) -> None:
        problem_locations = MalformedOptionalBlockError.get_marker_row(format_string, i, open_position)
        super().__init__(
            f"""Malformed optional block. No {{placeholders}} found in range {open_position, i}).
'{format_string}'
 {problem_locations}
{_hint}""".strip()
        )


class BadDelimiterError(MalformedOptionalBlockError):
    """Errors raised due to mismatched delimiters."""

    def __init__(self, format_string: str, i: int, open_position: int) -> None:
        problem_locations = MalformedOptionalBlockError.get_marker_row(format_string, i, open_position)

        if i == -1:
            super().__init__(
                f"""Malformed optional block. Optional block opened at i={open_position} was never closed.
'{format_string}'
 {problem_locations}""".strip()
            )
        else:
            info = (
                "there is no block to close"
                if open_position == -1
                else f"nested optional blocks are not supported (opened at {open_position})"
            )

            super().__init__(
                f"""Malformed optional block. Got '{format_string[i]}' at {i=}, but {info}.
    '{format_string}'
     {problem_locations}
{_hint}""".strip()
            )


@_dataclass(frozen=True)
class Element:
    """Information about a single block in a ``Format`` specification."""

    part: str
    """String literal."""
    placeholders: _List[str]
    """Placeholder names in `part`, if any."""
    required: bool
    """Flag indicating whether the element may be excluded."""

    @property
    def positional_part(self) -> str:
        """Return a positional version of the `part` attribute."""
        if not self.placeholders:
            return self.part

        return self.part.format(**{p: "{}" for p in self.placeholders})

    @staticmethod
    def make(s: str, in_optional_block: bool) -> "Element":
        """Create an ``Element`` from an input string `s`.

        Args:
            s: Input data.
            in_optional_block: Flag indicating whether `s` was found inside an optional block.

        Returns:
            A new ``Element``.
        """
        parsed_block = s.replace("\\[", "[").replace("\\]", "]")
        placeholders = [x[1] for x in _formatter.parse(parsed_block) if x[1]]

        return Element(
            parsed_block,
            placeholders,
            not (placeholders and in_optional_block),
        )


def verify_delimiters(format_string: str) -> None:
    """Verify that optional blocks are properly formatted.

    Args:
        format_string: User input string.

    Raises:
        BadDelimiterError: For unbalanced optional block delimitation characters.
    """
    open_position = -1

    for i in range(len(format_string)):
        if not _is_delimiter(format_string, i):
            continue

        char = format_string[i]

        if char == OPTIONAL_BLOCK_START_DELIMITER:
            if open_position != -1:
                raise BadDelimiterError(format_string, i, open_position)
            open_position = i
        else:
            if open_position == -1:
                raise BadDelimiterError(format_string, i, -1)
            open_position = -1

    if open_position != -1:
        raise BadDelimiterError(format_string, -1, open_position)


def get_elements(format_string: str) -> List[Element]:
    """Split a format string into elements.

    Args:
        format_string: User input string.

    Returns:
        A list of parsed elements.

    Raises:
        BadDelimiterError: For unbalanced optional block delimitation characters.
        UnusedOptionalBlockError: If optional blocks are defined without placeholders.
    """
    if not format_string:
        return [Element("", [], required=True)]

    verify_delimiters(format_string)

    delimiter_idx = [i for i in range(1, len(format_string)) if _is_delimiter(format_string, i)]

    delimiter_idx.append(len(format_string))

    ans: _List[Element] = []
    in_optional_block = _is_delimiter(format_string, 0)
    prev_idx = int(in_optional_block)
    for idx in delimiter_idx:
        if prev_idx != idx:
            element = Element.make(format_string[prev_idx:idx], in_optional_block)

            if in_optional_block and not element.placeholders:
                raise UnusedOptionalBlockError(format_string, idx, prev_idx - 1)

            ans.append(element)

        prev_idx = idx + 1
        in_optional_block = not in_optional_block

    return ans


def _is_delimiter(s: str, i: int) -> bool:
    char = s[i]

    if char not in (
        OPTIONAL_BLOCK_START_DELIMITER,
        OPTIONAL_BLOCK_END_DELIMITER,
    ):
        return False

    escaped = i > 0 and s[i - 1] == OPTIONAL_BLOCK_DELIMITER_ESCAPED
    return not escaped
