"""Translation of IDs with flexible formatting and name matching.

For and introduction to translation, see :ref:`translation-primer` and :ref:`mapping-primer`.
"""
from rics.translation._config_utils import ConfigMetadata
from rics.translation._translator import Translator
from rics.translation.factory import TranslatorFactory

__all__ = ["Translator", "TranslatorFactory", "ConfigMetadata"]
