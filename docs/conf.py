"""Sphinx configuration."""
# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import shutil
from importlib import import_module

from docutils.nodes import Text, reference

import rics
from rics._internal_support.changelog import split_changelog

type_modules = (
    "rics.mapping.types",
    "rics.translation.types",
    "rics.translation.fetching.types",
    "rics.utility.collections.dicts",
    "rics.utility.collections.misc",
)

for tm in type_modules:
    import_module(tm)


def callback(_app, _env, node, _contnode):  # noqa
    reftarget = node.get("reftarget")
    for m in type_modules:
        if reftarget.startswith(m):
            ans_hax = reference(refuri=m + ".html#" + reftarget, reftitle=reftarget)
            ans_hax.children.append(Text(reftarget.rpartition(".")[-1]))
            return ans_hax
    return None


def setup(app):  # noqa
    app.connect("missing-reference", callback)  # Fixes linking of typevars


# If extensions (or modules to document with autodoc) are in another
# directory, add these directories to sys.path here. If the directory is
# relative to the documentation root, use os.path.abspath to make it
# absolute, like shown here.
#


# -- Project information -------------------------------------------------------

# General information about the project.

project = rics.__title__
copyright = rics.__copyright__  # noqa: A001
author = rics.__author__
# The version info for the project you're documenting, acts as replacement
# for |version| and |release|, also used in various other places throughout
# the built documents.
#
# The full version, including alpha/beta/rc tags.
release = rics.__version__
# The short X.Y version.
version = ".".join(release.split(".")[:2])

# -- General configuration -----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autodoc.typehints",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosectionlabel",
    "nbsphinx",
    "sphinx.ext.mathjax",
    "myst_parser",
]
autosummary_ignore_module_all = False
autosummary_imported_members = True
# autoclass_content = "both"  # Add __init__ doc (ie. params) to class summaries
html_show_sourcelink = False  # Remove 'view source code' from top of page (for html, not python)
autodoc_inherit_docstrings = True  # If no docstring, inherit from base class
set_type_checking_flag = True  # Enable 'expensive' imports for sphinx_autodoc_typehints
nbsphinx_allow_errors = True  # Continue through Jupyter errors
# autodoc_typehints = "description" # Sphinx-native method. Not as good as sphinx_autodoc_typehints
add_module_names = False  # Remove namespaces from class/method signatures

suppress_warnings = [
    "autosectionlabel.*",  # https://github.com/sphinx-doc/sphinx/issues/7697
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    "_build",
    "_templates",
    "Thumbs.db",
    ".DS_Store",
    "**.ipynb_checkpoints",
]

# -- Options for HTML output ---------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "pydata_sphinx_theme"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.

html_theme_options = {
    "github_url": "https://github.com/rsundqvist/rics",
    "icon_links_label": "Quick Links",
    "use_edit_page_button": False,
    "navigation_with_keys": False,
    "show_toc_level": 1,
    "navbar_end": ["navbar-icon-links"],  # Dark mode doesn't work properly; disable it
}

# Used by pydata_sphinx_theme. Partially stolen from https://mne.tools/stable/index.html
html_context = {
    "github_user": "rsundqvist",
    "github_repo": "rics",
    "github_version": "master",
    "display_github": True,  # Integrate GitHub
    "conf_py_path": "/docs/",  # Path in the checkout to the docs root
    "default_mode": "light",  # Dark mode doesn't work properly; disable it
    "carousel": [
        dict(
            title="Performance",
            text="Convenience functions related to performance testing.",
            url="_autosummary/rics.performance.html",
            img="_static/performance.png",
            alt="Performance testing API documentation.",
        ),
        dict(
            title="Cookbook",
            text="Like copy-pasting? Me too!",
            url="documentation/examples/notebooks/cookbook/translation.html",
            img="_static/chef.png",
        ),
        dict(
            title="ID Translation",
            text="API documentation for the Translator and related classes.",
            url="_autosummary/rics.translation.html#rics.translation.Translator.translate",
            img="_static/translation.png",
            alt="Translation API documentation.",
        ),
        dict(
            title="Mapping",
            text="API documentation for the Mapper and related classes.",
            url="_autosummary/rics.mapping.html#rics.mapping.Mapper",
            img="_static/mapping.png",
            alt="Mapping API documentation.",
        ),
        dict(
            title="Utilities",
            text="Various utility methods.",
            url="_autosummary/rics.utility.html",
            img="_static/toolbox.png",
        ),
        dict(
            title="Translator Config",
            text="TOML format documentation.",
            url="documentation/translator-config.html",
            img="_static/toml-config.png",
            alt="Translator TOML config documentation.",
        ),
    ],
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static", "_images"]
html_css_files = ["style.css"]
html_logo = "logo-text.png"
html_favicon = "logo-icon.png"

# -- Nitpicky configuration ----------------------------------------------------
nitpicky = True
nitpick_ignore = [
    ("py:class", "re.Pattern"),
    ("py:class", "module"),
]

# -- Autodoc configuration -----------------------------------------------------
autodoc_typehints = "signature"
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "member-order": "bysource",
    "show-inheritance": True,
}

# -- Intersphinx configuration -------------------------------------------------
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pandas": ("http://pandas.pydata.org/pandas-docs/stable/", None),
    "sqlalchemy": ("https://docs.sqlalchemy.org/en/14/", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
}

# -- Gallery configuration -------------------------------------------------
sphinx_gallery_conf = {
    "sphinx_gallery_conf": "*.png",
    "gallery_dirs": ["_tiles"],
}

# -- Nbsphinx
nbsphinx_execute = "never"

shutil.copytree("../jupyterlab/demo/", "documentation/examples/notebooks", dirs_exist_ok=True)

split_changelog("changelog", "../CHANGELOG.md")
