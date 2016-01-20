==========
 Settings
==========

If you're interested in changing Holocron's defaults then you're at the
right place! This section covers basic (core) settings available for you.

Holocron configuration is a very simple task. All settings are stored in
one YAML file. By default, it's called ``_config.yml`` and should be
located in current working directory. However you can pass any file
via CLI (see ``--conf`` argument).

There are five main sections of settings:

* ``site``
* ``encoding``
* ``paths``
* ``theme``
* ``ext``

Let's take a closer look!


Site
====

This section is, probably, most commonly used one. It's responsible for
such base things like site 'title', its 'author' and 'URL'.

Example:

.. code:: yaml

    site:
      title:    Kenobi's Thoughts
      author:   Obi-Wan Kenobi
      url:      http://obi-wan.jedi


Encoding
========

It's a common practice to use Unicode everywhere in general, and UTF-8 as
file encoding in particular. Holocron isn't exception here, so UTF-8 is
used as default encoding for source content and produced HTMLs. However,
if by some reason it doesn't suite you, see the following example how
you can change it according to your needs.

Example:

.. code:: yaml

    encoding:
      content:  utf-8
      output:   utf-8


Paths
=====

The ``paths`` section allows to change default paths used by Holocron for
different purposes.

Example:

.. code:: yaml

    paths:
      content:  {here}/
      output:   {here}/_build
      theme:    {here}/_theme

where

* ``content`` -- a path where to search for posts, pages, etc
* ``output`` -- a path where to put produced HTMls
* ``theme`` -- a path where to look for user theme

The section supports the ``{here}`` macro which would be resolved into
a path to directory with your ``_config.yml``.

.. deprecated:: 0.3.0

    The ``theme`` option is deprecated in favor of ``user-theme`` extension.
    Please check out :ref:`user-theme` docs for details.


Theme
=====

.. note::

    Settings listed bellow are **only applied** for default Holocron
    theme. If you use some third-party one, please check out its
    documentation.

Well, the section contains theme specific settings. They are passed to
templates "As Is".

Example:

.. code:: yaml

    theme:
      navigation: !!pairs
        - about: /about
        - feed:  /feed.xml

      copyright: >
        &copy; 19 BBY, Obi-Wan Kenobi

      ribbon:
        text:  Star On GitHub
        link:  https://github.com/ikalnitsky/holocron

      twitter_cards:
        username: twitter

      counters:
        google_analytics: XX-XXXXXXXX-X
        yandex_metrika: XXXXXXX


where

* ``navigation`` -- a list to be shown on theme's navigation bar; it's
  usually used for putting top-level pages, or some other useful links
  such as 'feed' or 'twitter'.

* ``copyright`` -- an HTML text that will be shown in footer section on
  each web page.

* ``ribbon`` -- a ribbon label that appears on top right corner, and that
  leads on some page you want to promote (e.g. twitter, github, etc).

* ``tiwtter_cards`` --  `Twitter Cards`_ is a technology for showing
  rich snippets in tweets if someone posts a link to your site.

  .. _Twitter Cards: https://dev.twitter.com/cards/overview

* ``counters`` -- setup your counters, and watch the stats about visitors.


Ext
===

.. note::

    See :ref:`extensions` page for extensions' settings.

The ``ext`` section is used to enable and configure Holocron's extensions.
This documentation page will cover only how to enable them. If you're
interested in extensions' setting, please consider the notice above.

In order to enable extension you have to only put its name to the ``enabled``
subsection.

Example:

.. code:: yaml

    ext:
      enabled:
        - markdown
        - restructuredtext
        - index
        - feed
        - sitemap
        - tags
        - my-super-puper-extension      # <- inserted by us

.. warning::

    You must list explicitly all extensions you want to be enabled. There's
    no inheritance for them. I.e. you can't do

    .. code:: yaml

        ext:
          enabled:
            - my-super-puper-extension      # <- inserted by us

    and expect that ``markdown``, ``feed`` and others are enabled.
