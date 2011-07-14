:Author: James Rowe <jnrowe@gmail.com>
:Date: 2011-06-13
:Copyright: GPL v3
:Manual section: 1
:Manual group: Developer

hubugs
======

Simple client for GitHub issues
-------------------------------

SYNOPSIS
--------

    hubugs [option]... <command>

DESCRIPTION
-----------

:mod:`hubugs` is a very simple client for working with GitHub's issue tracker.
It allows you to perform all the issue related tasks you'd normally perform from
the command line.

OPTIONS
-------

--version
    show program's version number and exit

-h, --help
    show program's help message and exit

-p <project>, --project=<project>
    GitHub project to operate on.  You can supply just ``<project>`` if you wish
    to work on one of your own projects, or ``<user>/<project>`` to operate on
    another user's repository.  Default is derived from the current repository,
    if possible.

Commands
--------

``list``
''''''''

List bugs for a project

-s <state>, --state=<state>
   state of bugs to operate on

-l <label>, --label=<label>
   list bugs with specified label

-o <order>, --order=<order>
   sort order for listing bugs

``search``
''''''''''

Search bugs reports in a project

-s <state>, --state=<state>
   state of bugs to operate on

-o <order>, --order=<order>
   sort order for listing bugs

``show``
''''''''

Show specific bug(s) from a project

-f, --full
   show bug including comments

-p, --patch
   display patches for pull requests

-b, --browse
   open bug in web browser

``open``
''''''''

Open a new bug in a project

-a label, --add label
   add label to issue

--stdin
   read message from standard input

``comment``
'''''''''''

Comment on an existing bug in a project

--stdin
   read message from standard input

-m <text>, --message=<text>
   comment text

``edit``
''''''''

Edit an existing bug in a project

--stdin
   read message from standard input

``close``
'''''''''

Close an existing bug in a project

--stdin
   read message from standard input

-m <text>, --message=<text>
   comment text

``reopen``
''''''''''

Reopen a previously closed bug in a project

--stdin
   read message from standard input

-m <text>, --message=<text>
   comment text


``label``
'''''''''

Perform labelling actions on an existing bug in a project

-a <label>, --add=<label>
   add label to issue

-r <label>, --remove=<label>
   remove label from issue

CONFIGURATION
-------------

You can specify the template set to use by defining a ``hubugs.templates``
setting in your git configuration files.  For example::

    ▶ git config --global hubugs.templates my_templates

You can also set project specific template sets by editing a repository's
config.  See :manpage:`git-config(1)`.

BUGS
----

None known.

AUTHOR
------

Written by `James Rowe <mailto:jnrowe@gmail.com>`__

RESOURCES
---------

Home page, containing full documentation: http://jnrowe.github.com/hubugs/

Issue tracker: https://github.com/JNRowe/hubugs/issues/

COPYING
-------

Copyright © 2010-2011  James Rowe.

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version.
