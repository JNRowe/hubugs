Background
==========

GitHub_ provide a great issue tracker for small projects.  It is simple, light
and fast.  There's only one problem for me, I prefer command line tools for
these tasks.

Luckily, the issue tracker exposes your data via a `thoroughly documented API`_,
so alternative interfaces are only a :abbr:`SMOP (Small Matter of Programming)`
away.

The requirements
----------------

I live at the command line, data that isn't easily manageable from there may as
well not exist in my eyes.  Therefore:

    A simple `command line interface`_ is priority one.

It is nice to customise the views of data, and improve the look and feel of a
view over time.  Therefore:

    Views must be customisable via simple templates_

Data display must be fast, and require the minimum possible network access.
Therefore:

    Network data must be `cached and compressed`_ where possible

.. _GitHub: https://github.com/
.. _thoroughly documented API: http://developer.github.com/v3/
.. _command line interface: https://pypi.python.org/pypi/aaargh/
.. _templates: http://jinja.pocoo.org/
.. _cached and compressed: http://code.google.com/p/httplib2/
