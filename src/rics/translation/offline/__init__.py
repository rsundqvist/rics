"""Translation using local data given at initialization."""
from rics.translation.offline._format import Format
from rics.translation.offline._format_applier import DefaultFormatApplier, FormatApplier
from rics.translation.offline._magic_dict import MagicDict
from rics.translation.offline._placeholder_overrides import PlaceholderOverrides
from rics.translation.offline._translation_map import TranslationMap

__all__ = ["Format", "FormatApplier", "DefaultFormatApplier", "PlaceholderOverrides", "TranslationMap", "MagicDict"]
