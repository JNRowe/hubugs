hubugs - Simple client for GitHub issues
========================================

Introduction
------------

``hubugs`` is a very simple client for working with `GitHub's issue tracker`_.

.. important::

   This package is in a *rapid* state of flux right now, as support for version
   3 of the `GitHub API`_ is added.  Be aware there may be some significant
   changes to the user interface coming soon!

Requirements
------------

``hubugs`` requires Python_ v2.6 or above.  ``hubugs``'s mandatory
dependencies outside of the standard library are argh_, blessings_, html2text_,
Jinja_, micromodels_, misaka_, Pygments_ and requests_.

Configuration
-------------

Before ``hubugs`` can operate on issues you must generate an OAuth_ token.
``hubugs`` provides functionality to do this::

    $ hubugs setup
    GitHub user? [JNRowe]
    GitHub password? <password>
    Support private repositories? (Y/n) y
    Configuration complete!

.. note::

   You can revoke the generated token at any time from the `GitHub settings`_
   page.

If you wish to set the authentication token from the command line you can
use the ``HUBUGS_TOKEN`` environment variable.  For example::

    $ HUBUGS_TOKEN=xxx hubugs open

Contributors
------------

I'd like to thank the following people who have contributed to
``hubugs``.

Patches
'''''''

<Your name here?>

Bug reports
'''''''''''

* Brandon Cady
* Sorin Ionescu

Ideas
'''''

* James Gray
* Matt Leighy
* Jules Marleau

If I've forgotten to include your name I wholeheartedly apologise.  Just
drop me a mail_ and I'll update the list!

Hacking
-------

Patches and `pull requests`_ are most welcome, but I'd appreciate it if you
could follow the guidelines below to make it easier to integrate your changes.
These are only guidelines however, and as such can be broken if the need arises
or you just want to convince me that your style is better.

* `PEP 8`_, the style guide, should be followed where possible.
* While support for Python versions prior to v2.6 may be added in the future if
  such a need were to arise, you are encouraged to use v2.6 features now.
* All new classes, methods and functions should be accompanied by new
  ``doctest`` examples and reStructuredText_ formatted descriptions.
* Tests *must not* span network boundaries, use of a mocking framework is
  acceptable.
* ``doctest`` tests in modules are only for unit testing in general, and should
  not rely on any modules that aren't in Python's standard library.
* Functional tests should be in the ``doc`` directory in reStructuredText_
  formatted files, with actual tests in ``doctest`` blocks.  Functional tests
  can depend on external modules, but those modules must be Open Source.

New examples for the ``doc`` directory are as appreciated as code changes.

Bugs
----

If you find any problems, bugs or just have a question about this package
either file an issue_ or drop me a mail_.

If you've found a problem please attempt to include a minimal testcase so
I can reproduce the problem, or even better a patch!

.. _GitHub's issue tracker: http://github.com/blog/411-github-issue-tracker
.. _GitHub API: http://developer.github.com/v3/
.. _Python: http://www.python.org/
.. _argh: http://pypi.python.org/pypi/argh/
.. _blessings: http://pypi.python.org/pypi/blessings/
.. _Jinja: http://jinja.pocoo.org/
.. _html2text: http://pypi.python.org/pypi/html2text/
.. _micromodels: http://pypi.python.org/pypi/micromodels/
.. _misaka: http://pypi.python.org/pypi/misaka/
.. _Pygments: http://pygments.org/
.. _requests: http://pypi.python.org/pypi/requests/
.. _OAuth: http://oauth.net/
.. _GitHub settings: https://github.com/settings/applications/
.. _pull requests: http://github.com/JNRowe/hubugs/issues
.. _PEP 8: http://www.python.org/dev/peps/pep-0008/
.. _reStructuredText: http://docutils.sourceforge.net/rst.html
.. _mail: jnrowe@gmail.com
.. _issue: http://github.com/JNRowe/hubugs/issues
