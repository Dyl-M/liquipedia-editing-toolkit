"""Sphinx configuration for the liquipedia-editing-toolkit documentation."""

# -- Project information -----------------------------------------------------

project = "liquipedia-editing-toolkit"
author = "Dylan Monfret"
# noinspection PyShadowingBuiltins
copyright = "2026, Dylan Monfret @Dyl-M"

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
    "sphinx_copybutton",
    "myst_parser",
]

templates_path = ["_templates"]

# -- Options for autodoc -----------------------------------------------------

autodoc_member_order = "bysource"
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}
autodoc_typehints = "signature"
autodoc_class_signature = "separated"

# -- Options for Napoleon (Google-style docstrings) --------------------------

napoleon_google_docstring = True
napoleon_numpy_docstring = False

# -- Options for sphinx-autodoc-typehints ------------------------------------

typehints_defaults = "braces"
always_use_bars_union = True

# -- Options for MyST (Markdown support) -------------------------------------

myst_enable_extensions = [
    "colon_fence",
    "deflist",
]

# -- Options for intersphinx -------------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# -- Options for HTML output -------------------------------------------------

html_theme = "furo"
html_title = "liquipedia-editing-toolkit"

html_theme_options = {
    "source_repository": "https://github.com/Dyl-M/liquipedia-editing-toolkit",
    "source_branch": "main",
    "source_directory": "_docs/sphinx/",
    "light_css_variables": {
        "color-brand-primary": "#072B4B",
        "color-brand-content": "#0A3D6B",
        "color-sidebar-brand-text": "#072B4B",
        "color-sidebar-link-text--top-level": "#072B4B",
        "color-link": "#0A3D6B",
        "color-link--hover": "#072B4B",
    },
    "dark_css_variables": {
        "color-brand-primary": "#5BA3D9",
        "color-brand-content": "#7BB8E3",
        "color-sidebar-brand-text": "#5BA3D9",
        "color-sidebar-link-text--top-level": "#5BA3D9",
        "color-link": "#7BB8E3",
        "color-link--hover": "#5BA3D9",
    },
}

html_sidebars = {
    "**": [
        "sidebar/brand.html",
        "sidebar/search.html",
        "sidebar/scroll-start.html",
        "sidebar/navigation.html",
        "sidebar/scroll-end.html",
    ],
}

# -- Source file suffixes ----------------------------------------------------

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
