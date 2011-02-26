User-visible changes
====================

.. contents::

0.4.0 - 2011-02-26
------------------

    * Format Markdown output using terminal escapes

0.3.0 - 2011-02-26
------------------

    * Renamed to ``gh_bugs``
    * Support for different ordering methods in list and search output
    * Add or remove multiple labels by repeating ``-add` or ``-remove`` option
    * Templates are searched for in ``XDG_DATA_HOME/gh_bugs/``, any ``gh_bugs``
      directory in ``XDG_DATA_DIRS`` and finally the Python package directory
    * Jinja_ is now required
    * If termcolor_ is installed coloured output is produced
    * Addition of a distutils_ ``setup.py``

.. _Jinja: http://jinja.pocoo.org/
.. _termcolor: http://pypi.python.org/pypi/termcolor/
.. _distutils: http://docs.python.org/install/index.html

0.2.0 - 2011-02-25
------------------

    * Support for using an editor to write comments and open issues.

0.1.0 - 2010-11-02
------------------

    * Initial release
