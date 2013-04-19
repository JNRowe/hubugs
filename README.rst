hubugs - Simple client for GitHub issues
========================================

.. image:: https://secure.travis-ci.org/JNRowe/hubugs.png?branch=master
   :target: http://travis-ci.org/JNRowe/hubugs

Introduction
------------

``hubugs`` is a very simple client for working with `GitHub's issue tracker`_.

.. important::

   This package is in a *rapid* state of flux right now, as support for version
   3 of the `GitHub API`_ is added.  Be aware there may be some significant
   changes to the user interface coming soon!

Requirements
------------

``hubugs`` requires Python_ v2.6 or newer, including Python 3.  ``hubugs``'s
mandatory dependencies outside of the standard library are aaargh_, blessings_,
html2text_, httplib2_, Jinja_ and Pygments_.

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

If you wish to set the authorisation token from the command line you can use the
``HUBUGS_TOKEN`` environment variable.  For example::

    $ HUBUGS_TOKEN=xxx hubugs open

Contributors
------------

I'd like to thank the following people who have contributed to ``hubugs``.

Patches
'''''''

* Ben Griffiths
* Matt Leighton

Bug reports
'''''''''''

* Brandon Cady
* Sorin Ionescu

Ideas
'''''

* James Gray
* Jules Marleau
* Siddiq Shamoon

If I've forgotten to include your name I wholeheartedly apologise.  Just drop me
a mail_ and I'll update the list!

Bugs
----

If you find any problems, bugs or just have a question about this package either
file an issue_ or drop me a mail_.

If you've found a problem please attempt to include a minimal testcase so I can
reproduce the problem, or even better a patch!

.. _GitHub's issue tracker: http://github.com/blog/411-github-issue-tracker
.. _GitHub API: http://developer.github.com/v3/
.. _Python: http://www.python.org/
.. _aaargh: http://pypi.python.org/pypi/aaargh/
.. _blessings: http://pypi.python.org/pypi/blessings/
.. _Jinja: http://jinja.pocoo.org/
.. _html2text: http://pypi.python.org/pypi/html2text/
.. _httplib2: http://pypi.python.org/pypi/httplib2
.. _Pygments: http://pygments.org/
.. _OAuth: http://oauth.net/
.. _GitHub settings: https://github.com/settings/applications/
.. _mail: jnrowe@gmail.com
.. _issue: http://github.com/JNRowe/hubugs/issues
