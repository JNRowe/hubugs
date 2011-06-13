Templates
=========

Output is produced from templates using Jinja_.  Before writing your own
templates you should read the awesome `Jinja template designer`_ documentation.

Template locations
------------------

Templates are loaded from directories in the following order:

* If it exists, ``${XDG_DATA_HOME:~/.local}/gh_bugs/templates``
* Any :file:`gh_bugs/templates` directory in the directories specified by
  :envvar:`XDG_DATA_DIRS`
* The package's ``templates`` directory

For information on the usage of :envvar:`XDG_DATA_HOME` and
:envvar:`XDG_DATA_DIRS` read `XDG Base Directory Specification`_

.. note::
   If you create some cool templates of your own please consider posting them in
   an issue_ or pushing them to a fork on GitHub_, so that others can benefit.

Precedence
----------

The first name match in the order specified above selects the template, so a
:file:`view/list.txt` in :file:`${XDG_DATA_HOME}/gh_bugs/templates` overrides
:file:`view/list.txt` provided by :mod:`gh_bugs`.

Naming
------

Templates are separated in to two groups.  The first group, ``view``, is for
templates used in directly producing consumable output(such as from the ``list``
subcommand).  The second group, ``edit``, is for templates used to generate
input files for editing text(such as in the ``open`` subcommand).

View group templates currently include:

* :file:`issue.txt` for formatting a single bug
* :file:`list.txt` for formatting list output

Edit group templates currently include:

* :file:`default.mkd` for general use, such as in commenting on a bug
* :file:`open.mkd` for opening(or editing) bugs

Data
----

The following variables are available for use in templates

View group
''''''''''

* ``bugs`` which contains the sorted list of bugs to display, if any
* ``columns`` which is the width of the current terminal window
* ``id_len`` which is set to the maximum length of the bug IDs to display
* ``state`` of the bugs being searched/listed
* ``term`` which is set to the search term being listed
* ``order`` which is the ordering method to use

Edit group
''''''''''

* ``title`` which will contain the current title in ``edit`` subcommand sessions
* ``body`` which will contain the current body in ``edit`` subcommand sessions

All groups
''''''''''

Jinja templates support object attribute and method access, so an individual
``bug`` object's ``created_at`` attribute can be called with a ``strftime``
method for custom date output.  For example, ``{{ bug.created_at.strftime("%a,
%e %b %Y %H:%M:%S %z") }}`` can be used to output an :rfc:`2822` date stamp.

If you're authoring your own templates and you find you need extra data for
their generation open an issue_.

Filters
-------

:mod:`gh_bugs` defines the following filters beyond the huge range of `built-in
filters`_ in Jinja_:

.. note::

   If you write extra filters that you believe could be of use to other
   :mod:`gh_bugs` users please consider posting them in an issue_ or pushing
   them to a fork on GitHub_, so that others can benefit from your work.

``colourise``
'''''''''''''

This filter applies a colour to text, if possible.  When directing output to a
pipe or using a terminal that is incapable of displaying colours the text is
passed through unchanged.

For example, to show a bug's ``title`` attribute in red::

.. code-block:: jinja

    {{ bug.title | colourise('red') }}

.. note::
   This filter is also available under the name ``colorize``.

``highlight``
'''''''''''''

This filter highlights text using Pygments_.  You can specify the lexer to
be used, and also the formatter.

For example, to highlight a chunk of text as Python::

    {{ text | highlight('python') }}

To do the same using the 256-colour mode of Pygments_::

    {{ text | highlight('python', 'terminal256') }}

``relative_time``
'''''''''''''''''

This filter is used to generate a human-readable relative timestamp from a
:class:`~python:datetime.datetime` object.

For example, to display a bug's ``created_at`` attribute as a relative time::

    {{ bug.created_at | relative_time }}

which could produce output such as::

    about two months ago

``term_markdown``
'''''''''''''''''

The purpose of this filter is to pretty print Markdown formatted text.  It only
handles headings, horizontal rules and emphasis currently.

In the default templates it is used to render bug bodies::

    {{ comment.body | wordwrap(break_long_words=False) | term_markdown }}

.. note::
   We pass the text through Jinja's built-in :func:`jinja:wordwrap` filter prior to
   formatting with ``term_markdown`` so that the terminal escape sequences
   aren't included in the line width calculations.

.. _Jinja: http://jinja.pocoo.org/
.. _Jinja template designer: http://jinja.pocoo.org/docs/templates/
.. _XDG Base Directory Specification: http://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html
.. _issue: https://github.com/JNRowe/gh_bugs/issues
.. _GitHub: https://github.com/JNRowe/gh_bugs/
.. _built-in filters: http://jinja.pocoo.org/docs/templates/#list-of-builtin-filters
.. _Pygments: http://pygments.org/
