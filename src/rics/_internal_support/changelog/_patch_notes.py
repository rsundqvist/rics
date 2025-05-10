import datetime
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True)
class PatchNotes:
    """Notes for a single release."""

    title: str
    """Title of the release, such as `'0.1.0'`."""
    date: str
    """Date of the release."""
    extras: list[str]
    """Extra content to append just below the title."""

    sections: dict[str, list[str]]
    """Subsections such as `'Added'` and `'Fixed'`."""

    def __iter__(self) -> Iterable[tuple[str, list[str]]]:
        for section in sorted(self.sections):
            lines = self.sections[section]
            if lines:
                yield section.title(), lines

    @classmethod
    def from_markdown(cls, raw: str) -> tuple[list[Self], dict[str, str]]:
        """Create ``PatchNotes`` and references from the lines of a Markdown file.

        Args:
            raw: Raw blob of ``CHANGELOG.md`` file.

        Returns:
            A tuple ``([patch_notes..], {version: github_link})``.

        Raises:
            ValueError: If there are duplicate subsections.

        """
        parts = raw.split("\n## ")[1:]  # First section is just the title itself.
        last_lines = parts[-1].splitlines()  # Last part has references that we need to extract.
        del parts[-1]

        parsed_notes = list(map(cls._consume, parts))

        last_section_lines: list[str] = []
        for references_start, line in enumerate(last_lines):
            if "]: http" in line:
                parsed_notes.append(cls._consume("\n".join(last_section_lines)))
                refs = {line.partition(": ")[0].strip(): line for line in last_lines[references_start:]}
                return parsed_notes, refs
            else:
                last_section_lines.append(line)

        raise ValueError("Failed to parse final section:\n", "\n".join(last_lines))

    @classmethod
    def _consume(cls, content: str) -> Self:
        title, _, the_rest = map(str.strip, content.partition("\n"))

        if "-" in title:
            title, _, date = title.partition("-")
            date = datetime.datetime.strptime(date.strip(), "%Y-%m-%d").strftime("%B %d, %Y")
        else:
            date = ""

        subsection_content_lines: list[list[str]] = list(map(str.splitlines, the_rest.split("### ")))
        extra = subsection_content_lines[0]

        sections = {section_lines[0]: section_lines[1:] for section_lines in subsection_content_lines[1:]}

        return cls(title.strip(), date.strip(), extra, sections)
