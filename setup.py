#!/usr/bin/env python
# coding: utf-8

from setuptools import setup, find_packages

from holocron import __version__ as holocron_version
from holocron import __license__ as holocron_license

setup(
    name='holocron',
    version=holocron_version,
    license=holocron_license,
    description='simple, lightweight and extendable static blog generator',
    url='http://github.com/ikalnitsky/holocron/',
    author='Igor Kalnitsky',
    author_email='igor@kalnitsky.org',

    long_description='{0}\n{1}'.format(
        open('README.rst', 'r', encoding='utf-8').read(),
        open('CHANGES', 'r', encoding='utf-8').read()),

    packages=find_packages(exclude=['tests']),
    test_suite='tests',
    zip_safe=False,

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
            'feed = holocron.ext.generators.feed:Feed',
            'index = holocron.ext.generators.index:Index',
            'sitemap = holocron.ext.generators.sitemap:Sitemap',
            'tags = holocron.ext.generators.tags:Tags',
        ],

        'holocron.ext.commands': [
            'init = holocron.ext.commands.init:Init',
            'build = holocron.ext.commands.build:Build',
            'serve = holocron.ext.commands.serve:Serve',
        ],
    },

    classifiers=[
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Internet :: WWW/HTTP',
    ],
)
