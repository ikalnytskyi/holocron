.. _faq:

=====
 FAQ
=====


Why The Name Holocron?
======================

Holocron (*short for holographic chronicle*) is a device in which Jedi
stored different data. In most cases, they used it as diary. 


How To Create Stylized Post / Page?
===================================

Holocron supports a YAML front matter for posts and pages where you can
specify the ``template`` attribute. The example below renders a blog post
using the ``yoda.html`` template.

.. code:: markdown

   ---
   template: yoda.html
   ---

   some content

.. note::

   Templates must be available in runtime, and the only way to make it
   happen is to use either a third party theme or :ref:`user-theme`.
