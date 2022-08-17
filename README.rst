=====================================
 Holocron: may the blog be with you!
=====================================

|pypi-version| |license|

Holocron is an extendable static blog generator powered by the Force. Like
others, it reads text files in various formats, renders them using templates
and produces a ready-to-publish static website which could be served by
Nginx or another web server. Unlike others, it tries to retrieve as many
information as possible from the filesystem. Its core follows the KISS
principle and any wheel reinventions were avoided during the process.

Feel the Force? Then use Holocron!

.. code:: bash

    $ [sudo] pip3 install holocron


Features
========

Here is an incomplete list of features:

* Supports `Markdown`_, `reStructuredText`_ & code syntax highlighting.
* Provides simple & powerful plugin system.
* Supports third-party themes via `Jinja2`_ templates.
* Generates both `Atom feed`_ and `sitemap.xml`_.
* Has clear and 100% mobile responsive default theme.
* Supports `Google Analytics`_.
* Has SEO friendly URLs.
* Provides a debug server to preview content.


Links
=====

* Source: https://github.com/ikalnytskyi/holocron
* Bugs: https://github.com/ikalnytskyi/holocron/issues


.. Links

.. _Markdown: http://daringfireball.net/projects/markdown/
.. _reStructuredText: http://docutils.sourceforge.net/rst.html
.. _Jinja2: http://jinja.pocoo.org
.. _Atom feed: http://en.wikipedia.org/wiki/Atom_(standard)
.. _sitemap.xml: http://www.sitemaps.org/
.. _Google Analytics: http://www.google.com/analytics/

.. Badges

.. |pypi-version| image:: https://img.shields.io/pypi/v/holocron.svg
   :target: https://pypi.python.org/pypi/holocron

.. |license| image:: https://img.shields.io/pypi/l/holocron.svg
   :target: https://pypi.python.org/pypi/holocron
