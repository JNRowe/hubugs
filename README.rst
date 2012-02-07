hubugs - Simple client for GitHub issues
========================================

Introduction
------------

``hubugs`` is a very simple client for working with `GitHub's issue tracker`_.

Requirements
------------

``hubugs`` requires Python_ v2.6 or above.  ``hubugs``'s mandatory
dependencies outside of the standard library are argh_, blessings_, github2_
v0.6 or newer, html2text_, Jinja_, misaka_ and Pygments_.

Configuration
-------------

Before using ``hubugs`` you must declare your authentication settings, so that
we can access the API.

You first need to define your GitHub user name::

    $ git config --global github.user username

And then you need to define your GitHub API token, this can be found in the
`account admin`_ tab of your GitHub `account page`_::

    $ git config --global github.token token

.. note::

   If you change your GitHub password your ``github.token`` setting will be
   invalid, and you must set it again.

If you wish to set the authentication information from the command line you can
use the ``GITHUB_USER`` and ``GITHUB_TOKEN`` environment variables.  For
example::

    $ GITHUB_USER=jnrowe GITHUB_TOKEN=xxx hubugs open

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
.. _Python: http://www.python.org/
.. _argh: http://pypi.python.org/pypi/argh/
.. _blessings: http://pypi.python.org/pypi/blessings/
.. _github2: http://pypi.python.org/pypi/github2/
.. _Jinja: http://jinja.pocoo.org/
.. _html2text: http://pypi.python.org/pypi/html2text/
.. _misaka: http://pypi.python.org/pypi/misaka/
.. _Pygments: http://pygments.org/
.. _account admin: https://github.com/account/admin
.. _account page: https://github.com/account
.. _pull requests: http://github.com/JNRowe/hubugs/issues
.. _PEP 8: http://www.python.org/dev/peps/pep-0008/
.. _reStructuredText: http://docutils.sourceforge.net/rst.html
.. _mail: jnrowe@gmail.com
.. _issue: http://github.com/JNRowe/hubugs/issues
