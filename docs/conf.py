# coding: utf-8
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
pygments_style = 'default'

# html settings
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
