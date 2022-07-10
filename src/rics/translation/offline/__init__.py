"""Offline (in-memory) translation classes."""
from rics.translation.offline._format import Format
from rics.translation.offline._format_applier import DefaultFormatApplier, FormatApplier
from rics.translation.offline._magic_dict import MagicDict
from rics.translation.offline._translation_map import TranslationMap

__all__ = [
    "Format",
    "FormatApplier",
    "DefaultFormatApplier",
    "TranslationMap",
    "MagicDict",
]
