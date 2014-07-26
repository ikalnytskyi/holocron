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


setup(
    name='holocron',
    version=holocron_version,
    description=(
        'Simple and extensible static blog generator'
    ),
    long_description=__doc__,
    license='BSD',
    url='http://github.com/ikalnitsky/holocron/',
    platforms=['Linux'],

    author='Igor Kalnitsky',
    author_email='igor@kalnitsky.org',

    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    test_suite='tests',

    install_requires=[
        # core parts
        'Jinja2 >= 2.7',
        'PyYAML >= 3.11',
        'stevedore >= 0.15',
        'Pygments >= 1.6',
        'watchdog >= 0.8.0',
        'dooku',

        # markdown converter
        'Markdown >= 2.4',
    ],
    dependency_links=[
        'git+https://github.com/ikalnitsky/dooku.git#egg=dooku',
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
            'feed = holocron.ext.generators.feed:Feed',
        ],

        'holocron.ext.commands': [
            'serve = holocron.ext.commands.serve:Serve',
            'build = holocron.ext.commands.build:Build',
        ],
    },

    classifiers=[
        'Environment :: Console',
        'Operating System :: OS Independent',
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: BSD License',
        'Intended Audience :: End Users/Desktop',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
)
