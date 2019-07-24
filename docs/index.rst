Welcome to Holocron!
====================

Holocron is an extendible static site generator powered by `the Force`_.
Like others, it reads text files in various formats, renders them using
templates and produces a *ready-to-publish* static website, which could
be served by Nginx or another web server. Unlike others, it's built
around the idea of `processors`_ and `pipelines`_. Its core follows the
`KISS`_ principle and no wheels have been reinvented during development.

Feel the Force? Then use Holocron!

.. code:: bash

   $ [sudo] python3 -m pip install holocron

.. _the Force: https://en.wikipedia.org/wiki/The_Force
.. _KISS: https://en.wikipedia.org/wiki/KISS_principle
.. _processors: /processors/
.. _pipelines: /

Features
--------

* Supports `CommonMark`_, `Markdown`_, `reStructuredText`_ and code syntax
  highlighting.

  .. _CommonMark: https://commonmark.org/
  .. _Markdown: https://daringfireball.net/projects/markdown/
  .. _reStructuredText: http://docutils.sourceforge.net/rst.html

* Provides easy-to-hook-up plugin system.

* Generates `RSS`_ and `Atom`_ feeds. Of course, `iTunes Podcast`_ protocol
  is also included.

  .. _RSS: https://en.wikipedia.org/wiki/RSS
  .. _Atom: https://en.wikipedia.org/wiki/Atom_(Web_standard)
  .. _iTunes Podcast: https://itunespartner.apple.com/podcasts

* Where can we go without `sitemap.xml <https://www.sitemaps.org/>`_?

* `Jinja2 <http://jinja.pocoo.org/>`_ powered custom themes.

* The default theme is clean and 100% mobile responsive.

---

Eager to get started? Just follow `the Quickstart guide </quickstart/>`_.
