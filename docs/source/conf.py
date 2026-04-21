# Configuration file for the Sphinx documentation builder.

import os
import sys
from pathlib import Path

# Add project root to path for autodoc
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# -- Project information -----------------------------------------------------

project = 'Quantum-Resource-Estimator (pyqres)'
copyright = '2024, Agony'
author = 'Agony'

# Read version from pyproject.toml
try:
    from importlib.metadata import version as pkg_version
    release = pkg_version('pyqres')
except Exception:
    release = '0.1.0'

version = release

# -- Language settings -------------------------------------------------------

language = 'zh_CN'

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
    'sphinx_copybutton',
    'myst_parser',
    'sphinx_autodoc_typehints',
]

templates_path = ['_templates']
html_static_path = ['_static']

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

html_theme = 'furo'

html_theme_options = {
    'sidebar_hide_name': False,
    'navigation_with_keys': True,
    'source_repository': 'https://github.com/IAI-USTC-Quantum/Quantum-Resource-Estimator',
    'source_branch': 'main',
    'source_directory': 'docs/source',
    'light_css_variables': {
        'font-stack': '"Noto Sans SC", "Noto Sans", sans-serif',
    },
    'dark_css_variables': {
        'font-stack': '"Noto Sans SC", "Noto Sans", sans-serif',
    },
}

html_context = {
    'display_github': True,
    'github_user': 'IAI-USTC-Quantum',
    'github_repo': 'Quantum-Resource-Estimator',
    'github_version': 'main',
    'conf_py_path': '/docs/source/',
}

# -- Options for autodoc ----------------------------------------------------

autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__',
    'show-inheritance': True,
}

autodoc_typehints = 'signature'
autodoc_typehints_format = 'short'

autosummary_generate = True

# -- Options for intersphinx -------------------------------------------------

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'sympy': ('https://docs.sympy.org/latest/', None),
}

# -- Napoleon settings -------------------------------------------------------

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True

# -- i18n settings -----------------------------------------------------------

locale_dirs = ['locale/']
gettext_compact = False
