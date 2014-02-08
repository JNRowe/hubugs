Frequently Asked Questions
--------------------------

Do you accept template contributions?
'''''''''''''''''''''''''''''''''''''

Yes, if they are somewhat general.  And, it is a great way to have me maintain
template compatibility for you in case something changes in a future version.

Either open an issue_ or push them to a fork on GitHub_.

.. _issue: https://github.com/JNRowe/hubugs/issues
.. _GitHub: https://github.com/JNRowe/hubugs/

Why is the wrapping broken in comments I make?
''''''''''''''''''''''''''''''''''''''''''''''

Unfortunately, GitHub have crippled the newline behaviour of Markdown.  If you
wrap your comments for readability then you'll be creating new paragraphs with
every single line.  There is very little that can be done locally to fix this.

The easiest way to workaround the issue is to disable wrapping in your text
editor for template files.  The files ``hubugs`` creates are easy to match for
automating this within your editor, just use ``$TMPDIR/hubugs-*.mkd``.

How do I create headlines when lines beginning with ``#`` are scrubbed?
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

Markdown syntax supports two different heading formats, and only one of them
requires a ``#`` at the start of a line.  Using the alternative setext_ format
is simple:

.. code-block:: rest

    Heading
    =======

    Sub-heading
    -----------

The other possibility, although not recommended, is to set a custom value for
`core.commentchar` in your ``git`` configuration settings.  program:`hubugs`
will honour the set value, and strip any lines that begin with that character.
You should note however that this is a recent addition to git, and other tools
may not work correctly with it set to a non-default value.

.. _setext: http://docutils.sourceforge.net/mirror/setext.html

I don't like your choice of template language
'''''''''''''''''''''''''''''''''''''''''''''

[It isn't really a question, but it has come up a couple of times.]

The use of Jinja_ should only be an issue if you wish to author your own
templates, if you're using the built-in templates you shouldn't notice Jinja_ at
all.  That said...

The use of Jinja_ seems to be an entry barrier to some people, but it isn't
going to change.  For the same -- invariably pointless and religious -- reasons
people prefer other templating engines *I* prefer Jinja_.

.. note::
   With all that said, I probably wouldn't be opposed to accepting patches
   supporting additional *optional* engines ;)

.. _Jinja: http://jinja.pocoo.org/
