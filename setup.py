#!/usr/bin/env python
# coding: utf-8

import os

from io import open
from setuptools import setup, find_packages

from holocron import __version__ as version
from holocron import __license__ as license


here = os.path.dirname(__file__)

with open(os.path.join(here, 'README.rst'), 'r', encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='holocron',
    version=version,

    description='An extendable static blog generator powered by the Force. =/',
    long_description=long_description,
    license=license,
    url='http://github.com/ikalnytskyi/holocron/',
    keywords='blog generator static markdown restructuredtext',

    author='Ihor Kalnytskyi',
    author_email='igor@kalnitsky.org',

    packages=find_packages(exclude=['docs', 'tests*']),
    test_suite='tests',
    include_package_data=True,
    zip_safe=False,

    install_requires=[
        'Jinja2   >= 2.7',      # core
        'PyYAML   >= 3.11',     # core
        'dooku    >= 0.3.0',    # core
        'Pygments >= 2.0',      # core since required for various converters
        'python-dateutil >= 2.7',
        'jsonpointer >= 2.0',
        'schema >= 0.6',

        'Markdown >= 2.4',      # deps of markdown converter
        'docutils >= 0.12',     # deps of restructuredtext converter
        'watchdog >= 0.8.0',    # deps of serve command
    ],
    tests_require=['mock >= 1.1.0'],
    python_requires='>=3.4',

    entry_points={
        'console_scripts': [
            'holocron = holocron.main:main',
        ],
        'holocron.ext': [
            'user-theme = holocron.ext:UserTheme',
        ],
        'holocron.ext.processors': [
            'source = holocron.ext.processors.source:process',
            'metadata = holocron.ext.processors.metadata:process',
            'pipeline = holocron.ext.processors.pipeline:process',
            'frontmatter = holocron.ext.processors.frontmatter:process',
            'prettyuri = holocron.ext.processors.prettyuri:process',
            'markdown = holocron.ext.processors.markdown:process',
            'restructuredtext = '
            '   holocron.ext.processors.restructuredtext:process',
            'atom = holocron.ext.processors.atom:process',
            'sitemap = holocron.ext.processors.sitemap:process',
            'index = holocron.ext.processors.index:process',
            'tags = holocron.ext.processors.tags:process',
            'commit = holocron.ext.processors.commit:process',
        ],
        'holocron.ext.commands': [
            'init = holocron.ext.commands.init:Init',
            'build = holocron.ext.commands.build:Build',
            'serve = holocron.ext.commands.serve:Serve',
            'run = holocron.ext.commands.run:Run',
        ],
    },

    classifiers=[
        'Environment :: Console',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',

        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Information Technology',

        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Terminals',

        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
