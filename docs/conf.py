# -*- coding: utf-8 -*-
"""
    Sphinx configuration file for building Holocron's documentation.
"""
from __future__ import unicode_literals

import re
import os
import sys


# add parent dir to PYTHONPATH for allowing import em's version
sys.path.append(os.path.abspath(os.pardir))
from holocron import __version__ as holocron_version


# project settings
project = 'Holocron'
copyright = '2015, the Holocron Team'
release = holocron_version
version = re.sub('[^0-9.]', '', release)

# sphinx settings
extensions = ['sphinx.ext.autodoc']
templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
exclude_patterns = ['_build']
pygments_style = 'sphinx'

# apply alabaster theme
import alabaster
html_theme_path = [alabaster.get_path()]
extensions = ['alabaster']
html_theme = 'alabaster'
html_sidebars = {
    '**': [
        'about.html',
        'navigation.html',
        'searchbox.html',
    ]
}
html_theme_options = {
    'logo': 'logo.svg',
    'logo_name': True,
    'logo_text_align': 'center',
    'description': 'May the blog be with you!',
    'show_powered_by': False,

    'github_user': 'ikalnitsky',
    'github_repo': 'holocron',
    'github_button': False,
    'github_banner': True,
}
html_static_path = ['_static']
