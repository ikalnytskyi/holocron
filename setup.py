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
        'Pygments >= 2.0',      # core since required for various converters
        'python-dateutil >= 2.7',
        'jsonpointer >= 2.0',
        'schema >= 0.6',
        'stevedore >=1.30',

        'Markdown >= 2.4',      # deps of markdown converter
        'docutils >= 0.12',     # deps of restructuredtext converter
        'feedgen  >= 0.7',      # deps of feed processor
        'watchdog >= 0.8.0',    # deps of serve command
    ],
    tests_require=['mock >= 1.1.0'],
    python_requires='>=3.4',

    entry_points={
        'console_scripts': [
            'holocron = holocron.main:main',
        ],
        'holocron.processors': [
            'source = holocron.processors.source:process',
            'metadata = holocron.processors.metadata:process',
            'pipeline = holocron.processors.pipeline:process',
            'frontmatter = holocron.processors.frontmatter:process',
            'prettyuri = holocron.processors.prettyuri:process',
            'markdown = holocron.processors.markdown:process',
            'restructuredtext = holocron.processors.restructuredtext:process',
            'feed = holocron.processors.feed:process',
            'sitemap = holocron.processors.sitemap:process',
            'archive = holocron.processors.archive:process',
            'commit = holocron.processors.commit:process',
            'jinja2 = holocron.processors.jinja2:process',
            'when = holocron.processors.when:process',
        ],
        'holocron.ext.commands': [
            'init = holocron.ext.commands.init:Init',
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
