.. _extensions:

============
 Extensions
============

Markdown
========

.. list-table::
   :stub-columns: 1
   :widths: 1 100

   * - Integrated
     - yes

   * - Description
     - Converts Markdown documents into HTML.

   * - File Extensions
     - ``.md``, ``.mkd``, ``.mdown``, ``.markdown``

   * - Syntax
     - https://daringfireball.net/projects/markdown/syntax

Holocron uses extended version of Markdown syntax, so you'll have fenced
code blocks, tables and much more out of the box. Markdown converter
could be configured through the ``_config.yml``,

.. code:: yaml

    ext:
      markdown:
        extensions: [ ... ]       # default: [codehilite, extra]

where ``ext.markdown.extensions`` is passed directly to Markdown library.
Please check out the full list of supported extensions here:

    https://pythonhosted.org/Markdown/extensions/index.html


reStructuredText
================

.. list-table::
   :stub-columns: 1
   :widths: 1 100

   * - Integrated
     - yes

   * - Description
     - Converts reStructuredText documents into HTML.

   * - File Extensions
     - ``.rst``, ``.rest``

   * - Syntax
     - http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html

reStructuredText converter doesn't support any options, except ones passed
to docutils library. They are tricky, worthless and for nerds. So only
a simple example is provided.

.. code:: yaml

    ext:
      restructuredtext:
        docutils:
          initial_header_level: 2      # start sections from <h2>


Creole (Wiki)
=============

.. list-table::
   :stub-columns: 1
   :widths: 1 100

   * - Integrated
     - no, requires holocron-creole_ to be installed

   * - Description
     - Converts Creole (Wiki) documents into HTML.

   * - File Extensions
     - ``.creole``

   * - Syntax
     - http://www.wikicreole.org/wiki/AllMarkup

Creole converter isn't distributed within Holocron due to its license.
So you need to install it first before using.

.. code:: bash

    $ [sudo] pip3 install holocron-creole

Then, just put ``creole`` to the list of enabled extensions and voilà!

The converter supports only one option:

.. code:: yaml

    ext:
      creole:
        syntax_highlight: true

When it's ``true`` (default), the ``code`` macro is provided for
sharing code snippets with syntax highlighting.

.. code:: text

    <<code ext=".py">>
        def add(x, y):
            return x + y
    <</code>>


.. _holocron-creole: https://pypi.python.org/pypi/holocron-creole


Feed
====

.. list-table::
   :stub-columns: 1
   :widths: 1 100

   * - Integrated
     - yes

   * - Description
     - Generates an Atom feed from posts.

Feed extension generates only an Atom feed, and supports the following
options:

.. code:: yaml

    ext:
      feed:
        save_as: feed.xml
        posts_number: 5

where

* ``save_as`` -- an output filename (path relative to output directory)
* ``posts_number`` -- a number of recent posts which appear in the feed


Sitemap
=======

.. list-table::
   :stub-columns: 1
   :widths: 1 100

   * - Integrated
     - yes

   * - Description
     - Generates a sitemap.xml from your posts and pages.

Produced ``sitemap.xml`` contains only links to posts and pages; neither
tags nor other garbage are in there.

No configuration is allowed, since ``sitemap.xml`` must be located in
the root of output directory.


Index
=====

.. list-table::
   :stub-columns: 1
   :widths: 1 100

   * - Integrated
     - yes

   * - Description
     - Generates an ``index.html`` in the output folder.

Index extension is intended to generate so called front page, since it's
what users see when they open the site. By default, it generates a list
of posts, but one may add a new template to render using the following
option:

.. code:: yaml

    ext:
      index:
        template: document-list.html


Tags
====

.. list-table::
   :stub-columns: 1
   :widths: 1 100

   * - Integrated
     - yes

   * - Description
     - Generates 'tags' pages with posts.

Tags extension generates an index page for each tag used in blog, which
contains a list of posts marked with the tag. It also makes tags clickable
in posts. The extension supports the following settings:

.. code:: yaml

    ext:
      tags:
        template: document-list.html
        output: tags/{tag}

where

* ``template`` -- a template to be used to render tags index pages
* ``output`` -- an output directory for tags index page


User Theme
==========

.. list-table::
   :stub-columns: 1
   :widths: 1 100

   * - Integrated
     - yes

   * - Description
     - Allows to setup external theme for content rendering.

When enabled, the ``_theme`` folder in current working directory will be
consumed as user theme. The path could be changed using the following
option:

.. code:: yaml

    ext:
      user-theme:
        path: {here}/_themes/my-awesome-theme

where

* ``{here}`` -- a macros that will be replaced by the path to directory with
  configuration file (i.e. ``_config.yml``)

.. note:: User Theme extension supersedes the core functionality, as well
          as ``paths.theme`` setting.
