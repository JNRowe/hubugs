Contributing
============

Pull requests are most welcome, but I’d appreciate it if you could follow the
guidelines below to make it easier to integrate your changes.  These are
guidelines however, and as such can be broken if the need arises or you just
want to convince me that your style is better.

* `PEP 8`_, the style guide, should be followed where possible
* `PEP 257`_, the docstring style guide, should be followed at all times
* While support for Python versions prior to v3.5 may be added in the future if
  such a need were to arise, you are encouraged to use v3.5 features now
* Aim to support Python 3.5+, but even if you can’t test all versions open
  a pull request anyway
* All new classes and methods should be accompanied by new tests, and Sphinx_
  ``autodoc``-compatible descriptions
* You should add tests for new functionality, and berate me for not writing
  enough tests at the outset
* Tests *must not* span network boundaries, use of a common mocking framework is
  encouraged

.. _PEP 8: http://www.python.org/dev/peps/pep-0008/
.. _PEP 257: http://www.python.org/dev/peps/pep-0257/
.. _Sphinx: http://sphinx.pocoo.org/
