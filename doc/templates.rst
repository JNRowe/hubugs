.. highlight:: jinja

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
the :file:`view/list.txt` provided in the :mod:`gh_bugs` package.

Naming
------

Templates are separated in to two groups.  The first group, ``view``, is for
templates used in directly producing consumable output(such as from the ``list``
subcommand).  The second group, ``edit``, is for templates used to generate
input files for editing text(such as in the ``open`` subcommand).

``view`` group templates currently include:

* :file:`issue.txt` for formatting a single bug
* :file:`list.txt` for formatting list output

``edit`` group templates currently include:

* :file:`default.mkd` for general use, such as in commenting on a bug
* :file:`open.mkd` for opening(or editing) bugs

Data
----

The following variables are available for use in templates

View group
''''''''''

.. data:: columns(int)

   The width of the current terminal window

``list.txt`` data
~~~~~~~~~~~~~~~~~

.. data:: bugs(list)

   Contains the sorted list of bugs to display, if any.  See
   :ref:`bug_objects-label`.

.. data:: id_len(int)

   Set to the maximum length of the bug IDs to display

.. data:: state(str)

   The bug states being searched/listed

.. data:: order(str)

   The display order

.. data:: term(str)

   The search term being listed, if any

``issue.txt`` data
~~~~~~~~~~~~~~~~~~

.. data:: bug(list)

   Contains the sorted list of bugs to display, if any.  See
   :ref:`bug_objects-label`

.. data:: comments(list)

   When displaying a single bug this contains the list of comments associated
   with a bug, if any.  See :ref:`comment_objects-label`

.. data:: full(bool)

   True, if the user provided the :option:`gh_bugs show -f` option

.. data:: patch(str)

   The content found at the location in :attr:`Bug.patch_url`, if the user
   provided the :option:`gh_bugs show -p` option

Edit group
''''''''''

.. data:: title(str)

   The current bug title in ``edit`` subcommand sessions.  See
   :attr:`Bug.title`

.. data:: body(str)

   The current bug body in ``edit`` subcommand sessions, if any.  See
   :attr:`Bug.body`

All groups
''''''''''

Jinja templates support object attribute and method access, so an individual
``bug`` object's :data:`~Bug.created_at` attribute can be called with a
:meth:`~datetime.datetime.strftime` method for custom date output.  For example,
``{{ bug.created_at.strftime("%a, %e %b %Y %H:%M:%S %z") }}`` can be used to
output an :rfc:`2822`-style date stamp.

If you're authoring your own templates and you find you need extra data for
their generation open an issue_.

Filters
-------

:mod:`gh_bugs` defines the following filters beyond the huge range of excellent
`built-in filters`_ in Jinja_:

.. note::

   If you write extra filters that you believe could be of use to other
   :mod:`gh_bugs` users please consider posting them in an issue_ or pushing
   them to a fork on GitHub_, so that others can benefit from your work.

``colourise``
'''''''''''''

This filter applies a colour to text, if possible.  This functionality requires
:pypi:`termcolor`, if the module is unavailable the filter is simply a no-op.

When directing output to a pipe or using a terminal that is incapable of
displaying colours the text is passed through unchanged.

For example, to show a bug's ``title`` attribute in red::

    {{ bug.title | colourise('red') }}

.. note::
   This filter is also available under the synonym ``colorize``.

``highlight``
'''''''''''''

This filter highlights text using Pygments_.  You can specify the lexer to
be used, and also the formatter.

For example, to highlight a chunk of text as Python::

    {{ text | highlight('python') }}

To do the same using the 256-colour mode of Pygments_::

    {{ text | highlight('python', 'terminal256') }}

See the output of :program:`pygmentize -L` for the list of available lexers and
formatters.

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

The purpose of this filter is to pretty print Markdown_ formatted text, which is
the format used by GitHub issues.  It only handles headings, horizontal rules
and emphasis currently.

In the default templates it is used to render bug bodies::

    {{ comment.body | wordwrap(break_long_words=False) | term_markdown }}

.. note::
   We pass the text through Jinja's built-in :func:`jinja:wordwrap` filter prior
   to formatting with ``term_markdown`` so that the terminal escape sequences
   aren't included in the line width calculations for wrapping.

.. _Jinja: http://jinja.pocoo.org/
.. _Jinja template designer: http://jinja.pocoo.org/docs/templates/
.. _XDG Base Directory Specification: http://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html
.. _issue: https://github.com/JNRowe/gh_bugs/issues
.. _GitHub: https://github.com/JNRowe/gh_bugs/
.. _built-in filters: http://jinja.pocoo.org/docs/templates/#list-of-builtin-filters
.. _Pygments: http://pygments.org/
.. _Markdown: http://daringfireball.net/projects/markdown/