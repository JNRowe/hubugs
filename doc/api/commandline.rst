.. module:: hubugs

Command line
============

.. note::

   The documentation in this section is aimed at people wishing to contribute to
   :mod:`hubugs`, and can be skipped if you are simply using the tool from the
   command line.

.. autofunction:: setup(globs, local)
.. autofunction:: list_bugs(globs, label, page, pull_requests, order, state)
.. autofunction:: search(globs, order, state, term)
.. autofunction:: show(globs, full, patch, patch_only, browse, bugs)
.. autofunction:: open_bug(globs, add, create, stdin, title, body)
.. autofunction:: comment(globs, message, stdin, bugs)
.. autofunction:: edit(globs, stdin, title, body, bugs)
.. autofunction:: close(globs, stdin, message, bugs)
.. autofunction:: reopen(globs, stdin, message, bugs)
.. autofunction:: label(globs, add, create, remove, list, bugs)
.. autofunction:: milestone(globs, milestone, bugs)
.. autofunction:: milestones(globs, order, state, create, list)
.. autofunction:: report_bug(globs)

.. autofunction:: main
