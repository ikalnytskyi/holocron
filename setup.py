#!/usr/bin/env python
# coding: utf-8
"""
$ holocron_

  Holocron is an easy and lightweight static blog generator, based on
  markup text and Jinja2 templates. It's written in Python trying to
  keep things simple and extensible.

  Holocron in two points:

  * simple and extensible
  * clear theme and markdown out of the box

  Read the docs for more information: http://holocron.readthedocs.org/
  Fork and contribute: https://github.com/ikalnitsky/holocron
"""
from setuptools import setup, find_packages

from holocron import __version__ as holocron_version
from holocron import __license__ as holocron_license


setup(
    name='holocron',
    version=holocron_version,
    license=holocron_license,
    description='simple and extensible static blog generator',
    long_description=__doc__,
    url='http://github.com/ikalnitsky/holocron/',
    platforms='any',

    author='Igor Kalnitsky',
    author_email='igor@kalnitsky.org',

    packages=find_packages(exclude=['tests']),
    test_suite='tests',

    install_requires=[
        # core parts
        'dooku >= 0.3.0',
        'Jinja2 >= 2.7',
        'PyYAML >= 3.11',
        'Pygments >= 1.6',
        'watchdog >= 0.8.0',

        # markdown converter
        'Markdown >= 2.4',
    ],

    entry_points={
        'console_scripts': [
            'holocron = holocron.main:main',
        ],

        'holocron.ext.converters': [
            'markdown = holocron.ext.converters.markdown:Markdown',
        ],

        'holocron.ext.generators': [
            'sitemap = holocron.ext.generators.sitemap:Sitemap',
            'blog = holocron.ext.generators.blog:Blog',
        ],

        'holocron.ext.commands': [
            'init = holocron.ext.commands.init:Init',
            'build = holocron.ext.commands.build:Build',
            'serve = holocron.ext.commands.serve:Serve',
        ],
    },

    classifiers=[
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: BSD License',

        'Environment :: Console',
        'Operating System :: OS Independent',

        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',

        'Programming Language :: Python :: Implementation :: CPython',
    ],
)
