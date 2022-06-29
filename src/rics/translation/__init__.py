"""Translation of IDs with flexible formatting and name matching."""
from rics.translation import factory, fetching, offline
from rics.translation._translator import Translator

__all__ = ["Translator", "factory", "fetching", "offline"]
