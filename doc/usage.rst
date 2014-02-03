Usage
=====

The :program:`hubugs` script is the main workhorse of :mod:`hubugs`.

Let's start with some basic examples:

.. code-block:: sh

    ▶ hubugs list  # List the open bugs for the current project
    Id Title
     5 Handle some GitHub markdown extensions [feature]
     6 Sphinx documentation tree [task]
     7 Support per project templates [feature]

    3 open bugs found

    ▶ hubugs search markdown  # Search for bugs matching markdown
    Id Title
     5 Handle some GitHub markdown extensions [feature]

    1 open bug found matching markdown

    ▶ hubugs show 6  # Show bug number 6
              Id: 6
           Title: Sphinx documentation tree
          Labels: task
         Created: yesterday by JNRowe
         Updated: yesterday
           State: open
        Comments: 0
    Pull request: No

    This project deserves some real user documentation, not just a few notes in
    `README.rst`.

    ▶ hubugs comment 6  # Comment on bug 6 using your editor

    ▶ hubugs comment -m"New comment." 6  # Add comment from command line

Options
-------

.. program:: hubugs

.. cmdoption:: --version

   show program's version number and exit

.. cmdoption:: -h, --help

   show program's help message and exit

.. cmdoption:: --pager <pager>

   pass output through a pager

.. cmdoption:: --no-pager

   do not pass output through pager

.. cmdoption:: -p <project>, --project=<project>

   GitHub project to operate on

.. cmdoption:: -u <url>, --host-url=<url>

   host to connect to, for GitHub Enterprise support

.. note::

   You can set a default value for the ``--pager`` and ``--host-url`` options by
   defining ``hubugs.pager`` or ``hubugs.host-url`` respectively in your ``git``
   configuration files.  Both global and project local settings are supported,
   see :manpage:`git-config(1)` for more information.

Commands
--------

``setup`` - Generate a new GitHub access token
''''''''''''''''''''''''''''''''''''''''''''''

.. program:: hubugs setup

::

    hubugs.py setup [-h] [--local]

.. cmdoption:: --local

   set access token for local repository only


``list`` - List bugs for a project
''''''''''''''''''''''''''''''''''

.. program:: hubugs list

::

    hubugs list [-h] [-s {open,closed,all}] [-l label]
        [-o {number,updated}]

.. cmdoption:: -s <state>, --state=<state>

   state of bugs to operate on

.. cmdoption:: -l <label>, --label=<label>

   list bugs with specified label

.. cmdoption:: -o <order>, --order=<order>

   sort order for listing bugs

.. cmdoption:: -p <number>, --page <number>

   page number

.. cmdoption:: -r, --pull-requests

   list only pull requests

``search`` - Search bugs reports in a project
'''''''''''''''''''''''''''''''''''''''''''''

.. program:: hubugs search

::

    hubugs search [-h] [-s {open,closed,all}]
        [-o {number,updated}]
        term

.. cmdoption:: -s <state>, --state=<state>

   state of bugs to operate on

.. cmdoption:: -o <order>, --order=<order>

   sort order for listing bugs

``show`` - Show specific bug(s) from a project
''''''''''''''''''''''''''''''''''''''''''''''

.. program:: hubugs show

::

    hubugs show [-h] [-f] [-p] bugs [bugs ...]

.. cmdoption:: -f, --full

   show bug including comments

.. cmdoption:: -p, --patch

   display patches for pull requests

.. cmdoption:: -o, --patch-only

   display only the patch content of pull requests

.. cmdoption:: -b, --browse

   open bug in web browser

``open`` - Open a new bug in a project
''''''''''''''''''''''''''''''''''''''

.. program:: hubugs open

::

    hubugs open [-h] [-a label] [--stdin] [title] [body]

.. cmdoption:: -a label, --add label

   add label to issue

.. cmdoption:: --stdin

   read message from standard input

``comment`` - Comment on an existing bug in a project
'''''''''''''''''''''''''''''''''''''''''''''''''''''

.. program:: hubugs comment

::

    hubugs comment [-h] [--stdin] [-m MESSAGE] bugs [bugs ...]

.. cmdoption:: --stdin

   read message from standard input

.. cmdoption:: -m <text>, --message=<text>

   comment text

``edit`` - Edit an existing bug in a project
''''''''''''''''''''''''''''''''''''''''''''

.. program:: hubugs edit

::

    hubugs edit [-h] [--stdin] [title] [body] bugs [bugs ...]

.. cmdoption:: --stdin

   read message from standard input

``close`` - Close an existing bug in a project
''''''''''''''''''''''''''''''''''''''''''''''

.. program:: hubugs close

::

    hubugs close [-h] [--stdin] [-m MESSAGE] bugs [bugs ...]

.. cmdoption:: --stdin

   read message from standard input

.. cmdoption:: -m <text>, --message=<text>

   comment text

``reopen`` - Reopen a previously closed bug in a project
''''''''''''''''''''''''''''''''''''''''''''''''''''''''

.. program:: hubugs reopen

::

    reopen [-h] [--stdin] [-m MESSAGE] bugs [bugs ...]

.. cmdoption:: --stdin

   read message from standard input

.. cmdoption:: -m <text>, --message=<text>

   comment text

``label`` - Perform labelling actions on an existing bug in a project
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

.. program:: hubugs label

::

    hubugs label [-h] [-a label] [-r label] bugs [bugs ...]

.. cmdoption:: -a <label>, --add=<label>

   add label to issue

.. cmdoption:: -r <label>, --remove=<label>

   remove label from issue

``milestone`` - Add an issue to a milestone
'''''''''''''''''''''''''''''''''''''''''''

.. program:: hubugs milestone

::

    hubugs milestone [-h] milestone [bugs [bugs ...]]

``milestones`` - Manage repository milestones
'''''''''''''''''''''''''''''''''''''''''''''

.. program:: hubugs milestones

::

    hubugs milestones [-h] [-o {due_date,completeness}] [-s {open,closed}]
        [-c milestone] [-l]

.. cmdoption:: -o <order>, --order=<order>

   sort order for listing bugs

.. cmdoption:: -s <state>, --state=<state>

   state of bugs to operate on

.. cmdoption:: -c <name>, --create=<name>

   create new milestone

.. cmdoption:: -l, --list

   list available milestones
