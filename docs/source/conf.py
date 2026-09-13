import os
import sys

sys.path.insert(0, os.path.abspath('../../src'))

project = 'wikimedia-abusefilter-accounts'
author = 'Max'
copyright = '2026, Max'
release = '0.1.0'
version = release

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
]

autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
    'member-order': 'bysource',
}
autodoc_member_order = 'bysource'
autodoc_typehints = 'description'
autodoc_mock_imports = ['toolforge']

html_context = {
    "display_github": True,
    "github_user": "MadMaxWP",
    "github_repo": "wikimedia-abusefilter-accounts",
    "github_version": "main",
    "conf_py_path": "/docs/source/",
}

html_theme = 'sphinx_rtd_theme'
