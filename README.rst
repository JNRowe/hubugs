gh-bugs - Simple client for GitHub issues
=========================================

Introduction
------------

``gh-bugs`` is a very simple client for working `GitHub's issue tracker`_.

Requirements
------------

``gh-bugs`` requires Python_ v2.6 or above. ``gh-bugs``'s mandatory
dependencies outside of the standard library are github2_ and termstyle_.

Configuration
-------------

.. TODO

Contributors
------------

I'd like to thank the following people who have contributed to
``gh-bugs``.

Patches
'''''''

Bug reports
'''''''''''

Ideas
'''''

If I've forgotten to include your name I wholeheartedly apologise.  Just
drop me a mail_ and I'll update the list!

Hacking
-------

Patches are most welcome, but I'd appreciate it if you could follow the
guidelines below to make it easier to integrate your changes.  These are
guidelines however, and as such can be broken if the need arises or you
just want to convince me that your style is better.

  * `PEP 8`_, the style guide, should be followed where possible.
  * While support for Python versions prior to v2.6 may be added in the
    future if such a need were to arise, you are encouraged to use v2.6
    features now.
  * All new classes, methods and functions should be accompanied by new
    ``doctest`` examples and reStructuredText_ formatted descriptions.
  * Tests *must not* span network boundaries, use of a mocking framework
    is acceptable.
  * ``doctest`` tests in modules are only for unit testing in general, and
    should not rely on any modules that aren't in Python's standard
    library.
  * Functional tests should be in the ``doc`` directory in
    reStructuredText_ formatted files, with actual tests in ``doctest``
    blocks.  Functional tests can depend on external modules, but those
    modules must be Open Source.

New examples for the ``doc`` directory are as appreciated as code changes.

Bugs
----

If you find any problems, bugs or just have a question about this package
either file an issue_ or drop me a mail_.

If you've found a problem please attempt to include a minimal testcase so
I can reproduce the problem, or even better a patch!

.. _GitHub's issue tracker: http://github.com/blog/411-github-issue-tracker
.. _Python: http://www.python.org/
.. _github2: http://pypi.python.org/pypi/github2/0.2.0
.. _termstyle: http://github.com/gfxmonk/termstyle
.. _PEP 8: http://www.python.org/dev/peps/pep-0008/
.. _reStructuredText: http://docutils.sourceforge.net/rst.html
.. _mail: jnrowe@gmail.com
.. _issue: http://github.com/JNRowe/gh-bugs/issues

..
    :vim: set ft=rst ts=4 sw=4 et:

