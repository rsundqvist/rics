import colorsys as original
import importlib
import sys


def test_reimport(unload_modules):
    unload_modules("colorsys", "never_imported")
    assert "colorsys" not in sys.modules
    assert importlib.import_module("colorsys") is not original


def test_restored():
    assert sys.modules["colorsys"] is original
