# -*- coding: utf-8 -*-
#
# wm documentation build configuration file, created by
# sphinx-quickstart on Sat Dec 28 20:34:13 2013.

import os
import sys

import wm

sys.path.append(os.path.abspath('../_theme'))

# -- General configuration -----------------------------------------------------

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.coverage', 'sphinx.ext.autosummary']
templates_path = ['_templates']
source_suffix = '.rst'
source_encoding = 'utf-8'
master_doc = 'index'
project = u'wm'
copyright = u'2013, Aaron Jacobs'
version = wm.__version__
release = wm.__version__
exclude_patterns = []

# -- Options for HTML output ---------------------------------------------------

html_theme = '_theme'
html_theme_path = ['..']
html_theme_options = {
    'show_navigation': 'false',
    'github_fork': 'atheriel/wm',
}
html_static_path = ['_static']
htmlhelp_basename = 'wmdoc'
