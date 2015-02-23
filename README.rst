Holocron - may the blog be with you!
====================================

:Source:    https://github.com/ikalnitsky/holocron
:Status:    |travis-ci|  |coveralls|


What Is Holocron?
-----------------

Holocron is a simple, lightweight and extendable static blog generator.

Like others, it reads text files in various formats, renders them using
templates and produces a ready-to-publish static website which could be
served by Nginx or another web server.

Unlike others, it tries to retrieve as many information as possible from
the file system. Its core follows the KISS principle and doesn't reinvent
the wheel.


Why Holocron?
------------

* Posts, pages, tags and feed are out-of-box.

* `Markdown`_ + code syntax highlighting.

* Themes (based on Jinja2_ template engine).

* It's `BSD Licensed`_!


How To Start?
-------------

Just follow the commands (see comments inline):

.. code:: bash

    $ [sudo] pip install holocron     # install the Holocron software

    $ mkdir -p path/to/my/blog        # prepare a directory for blog
    $ cd path/to/my/blog              # and enter it

    $ holocron init                   # initialize it with an example content
    $ holocron build                  # compilte its content to HTML
    $ holocron serve                  # run development server for preview


Why The Name Holocron?
----------------------

Holocron (short for holographic chronicle) is a device in which Jedi
stored different data. In most cases, they used it as diary.


.. _Markdown: http://daringfireball.net/projects/markdown/
.. _Jinja2: http://jinja.pocoo.org
.. _BSD Licensed: http://choosealicense.com/licenses/bsd-3-clause/

.. |travis-ci| image::
       https://travis-ci.org/ikalnitsky/holocron.svg?branch=master
   :target: https://travis-ci.org/ikalnitsky/holocron
   :alt: Travis CI: continuous integration status

.. |coveralls| image::
       https://coveralls.io/repos/ikalnitsky/holocron/badge.png?branch=master
   :target: https://coveralls.io/r/ikalnitsky/holocron?branch=master
   :alt: Coverall: code coverage status
