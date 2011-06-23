Alternatives
============

Before diving in and spitting out this package I looked at the alternatives
below.  If I have missed something please drop me a mail_.

Both the ``ghi`` and ``github-cli`` packages listed below are very useful, and
quite usable, clients for GitHub issues.  You should definitely try them out
before making a decision on what to use, and this would also allow you to
highlight any possible bias I may have shown in comparing them ;)

``ghi``
-------

ghi_ is a great issues client, written in Ruby_.

I personally didn't like the "feel" of the command line interface, and wanted
slightly different output.

:mod:`hubugs` provides the following advantages:

* Easily customisable output
* HTTP compression support
* On-disk cache support
* Pull request integration

and has the following disadvantages:

* No built-in pager support, but that is only a less_ pipe or shell function
  away
* :mod:`hubugs` requires a significant number of external packages, which may
  be a problem for some users

``github-cli``
--------------

github-cli_ is a fantastic command-line client for GitHub's issues, written in
Python_.  I really liked ``github-cli`` to the extent of authoring a few
patches, but just didn't find it comfortable to use in the long run [#]_.

:mod:`hubugs` provides the following advantages:

* Easily customisable output
* HTTP compression support
* On-disk cache support
* Pull request integration
* Uses the same method as ``git`` for choosing an editor to use, which will only
  affect you if you a custom editor for interacting with ``git``

and has the following disadvantages:

* No built-in pager support, but that is only a less_ pipe or shell function
  away
* :mod:`hubugs` requires a significant number of external packages, which may
  be a problem for some users

.. [#] If you look at the timeline for the `hubugs repository`_ and my
   `github-cli fork`_ you'll see I was using ``github-cli`` for a few months
   after spiking :mod:`hubugs`.

.. _mail: jnrowe@gmail.com
.. _ghi: https://github.com/stephencelis/ghi
.. _ruby: http://www.ruby-lang.org/
.. _less: http://www.greenwoodsoftware.com/less/
.. _github-cli: http://packages.python.org/github-cli/
.. _Python: http://python.org/
.. _hubugs repository: https://github.com/JNRowe/hubugs
.. _github-cli fork: https://github.com/JNRowe/github-cli
