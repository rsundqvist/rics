"""Alias of :mod:`rics.cli`."""

from .cli import main

# The docs prefer no guard, but only so a zipapp root behaves the same. Without one, tools that import every submodule
# (e.g. Sphinx autosummary) run the CLI with their own argv.
if __name__ == "__main__":
    main()
