Usage
=====

The :program:`gh_bugs` script is the main workhorse of :mod:`gh_bugs`.

Let's start with some basic examples:

.. code-block:: sh

    ▶ gh_bugs list  # List the open bugs for the current project
    Id Title
     5 Handle some GitHub markdown extensions [feature]
     6 Sphinx documentation tree [task]
     7 Support per project templates [feature]

    6 open bugs found
    ▶ gh_bugs search markdown  # Search for bugs matching markdown
    Id Title
     5 Handle some GitHub markdown extensions [feature]

    1 open bug found matching markdown
    ▶ gh_bugs show 6  # Show bug number 6
              Id: 6
           Title: Sphinx documentation tree
          Labels: task
         Created: yesterday by JNRowe
         Updated: yesterday
           State: open
        Comments: 0
           Votes: 0
    Pull request: No

    This project deserves some real user documentation, not just a few notes in
    `README.rst`.
    ▶ gh_bugs comment 6  # Comment on bug 6 using your editor
    ▶ gh_bugs comment -m"New comment." 6  # Add comment from command line

Options
-------

.. program:: gh_bugs

.. cmdoption:: --version

   show program's version number and exit

.. cmdoption:: -h, --help

   show this help message and exit

.. cmdoption:: -p <project>, --project=<project>

   GitHub project to operate on

Commands
--------

``list``
''''''''

.. program:: gh_bugs-list

::
  
    gh_bugs list [-h] [-s {open,closed,all}] [-l label]
        [-o {number,updated,votes}]

.. cmdoption:: -s <state>, --state=<state>

   state of bugs to operate on

.. cmdoption:: -l <label>, --label=<label>

   list bugs with specified label

.. cmdoption::  -o <order>, --order=<order>

   sort order for listing bugs

``search``
''''''''''

.. program:: gh_bugs-search

::

    gh_bugs search [-h] [-s {open,closed,all}]
        [-o {number,updated,votes}]
        term

.. cmdoption:: -s <state>, --state=<state>

   state of bugs to operate on

.. cmdoption::  -o <order>, --order=<order>

   sort order for listing bugs

``show``
''''''''

.. program:: gh_bugs-show

::

    gh_bugs show [-h] [-f] [-p] bugs [bugs ...]

.. cmdoption::  -f, --full

   show bug including comments

.. cmdoption::  -p, --patch

   display patches for pull requests

``open``
''''''''

.. program:: gh_bugs-open

::

    gh_bugs open [-h] [--stdin] [title] [body]

.. cmdoption:: --stdin

   read message from standard input

``comment``
'''''''''''

.. program:: gh_bugs-comment

::

    gh_bugs comment [-h] [--stdin] [-m MESSAGE] bugs [bugs ...]

.. cmdoption:: --stdin

   read message from standard input

.. cmdoption:: -m <text>, --message=<text>

   comment text

``edit``
''''''''

.. program:: gh_bugs-edit

::

    gh_bugs edit [-h] [--stdin] [title] [body] bugs [bugs ...]

.. cmdoption:: --stdin

   read message from standard input

``close``
'''''''''

.. program:: gh_bugs-close

::

    gh_bugs close [-h] [--stdin] [-m MESSAGE] bugs [bugs ...]

.. cmdoption:: --stdin

   read message from standard input

.. cmdoption:: -m <text>, --message=<text>

   comment text

``reopen``
''''''''''

.. program:: gh_bugs-reopen

::

    reopen [-h] [--stdin] [-m MESSAGE] bugs [bugs ...]

.. cmdoption:: --stdin

   read message from standard input

.. cmdoption:: -m <text>, --message=<text>

   comment text


``label``
'''''''''

.. program:: gh_bugs-label

::

    gh_bugs label [-h] [-a label] [-r label] bugs [bugs ...]

.. cmdoption:: -a <label>, --add=<label>

   add label to issue

.. cmdoption:: -r <label>, --remove=<label>

   remove label from issue
