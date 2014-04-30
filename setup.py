#!/usr/bin/env python
# coding: utf-8
"""
Holocron
--------

Holocron is an easy and lightweight static blog generator, based on markup
text and Jinja2 templates.


How To Install?
```````````````

.. code:: bash

    $ [sudo] pip install holocron


Useful Links
````````````

* `documentation <http://holocron.readthedocs.org/>`_
* `source code <https://github.com/ikalnitsky/holocron>`_

"""
from setuptools import setup, find_packages
from holocron import __version__ as holocron_version


setup(
    name='holocron',
    version=holocron_version,
    description=(
        'Holocron is an easy and lightweight static blog generator, based '
        'on markup text and Jinja2 templates.'
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
