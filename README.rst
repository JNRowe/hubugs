hubugs - Simple client for GitHub issues
========================================

|status| |travis| |coveralls| |pypi| |pyvers| |readthedocs| |develop|

.. warning::

   I don’t really use GitHub anymore, so this package is somewhat orphaned.  It
   should still work *and* I will fix bugs when they’re pointed out, but
   ``hubugs`` is frankly quite a low priority for me.

Introduction
------------

``hubugs`` is a very simple client for working with `GitHub’s issue tracker`_.

Requirements
------------

``hubugs`` requires Python_ v3.5 or newer.  ``hubugs``’s mandatory dependencies
outside of the standard library are click_, html2text_, httplib2_, Jinja_,
misaka_ and Pygments_.

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

I’d like to thank the following people who have contributed to ``hubugs``.

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

If I’ve forgotten to include your name I wholeheartedly apologise.  Just drop me
a mail_ and I’ll update the list!

Bugs
----

If you find any problems, bugs or just have a question about this package either
file an issue_ or drop me a mail_.

If you’ve found a problem please attempt to include a minimal testcase so I can
reproduce the problem, or even better a patch!

.. _GitHub’s issue tracker: http://github.com/blog/411-github-issue-tracker
.. _Python: http://www.python.org/
.. _click: https://pypi.org/projects/click/
.. _Jinja: http://jinja.pocoo.org/
.. _html2text: https://pypi.org/projects/html2text/
.. _httplib2: https://pypi.org/projects/httplib2/
.. _misaka: https://pypi.org/projects/misaka/
.. _Pygments: http://pygments.org/
.. _OAuth: http://oauth.net/
.. _GitHub settings: https://github.com/settings/applications/
.. _mail: jnrowe@gmail.com
.. _issue: http://github.com/JNRowe/hubugs/issues

.. |travis| image:: https://img.shields.io/travis/JNRowe/hubugs.png
   :target: https://travis-ci.org/JNRowe/hubugs
   :alt: Test state on master

.. |develop| image:: https://img.shields.io/github/commits-since/JNRowe/hubugs/latest.png
   :target: https://github.com/JNRowe/hubugs
   :alt: Recent developments

.. |pyvers| image:: https://img.shields.io/pypi/pyversions/hubugs.png
   :alt: Supported Python versions

.. |status| image:: https://img.shields.io/pypi/status/hubugs.png
   :alt: Development status

.. |coveralls| image:: https://img.shields.io/coveralls/github/JNRowe/hubugs/master.png
   :target: https://coveralls.io/repos/JNRowe/hubugs
   :alt: Coverage state on master

.. |pypi| image:: https://img.shields.io/pypi/v/hubugs.png
   :target: https://pypi.org/project/hubugs/
   :alt: Current PyPI release

.. |readthedocs| image:: https://img.shields.io/readthedocs/hubugs/stable.png
   :target: https://hubugs.readthedocs.io/
   :alt: Documentation
