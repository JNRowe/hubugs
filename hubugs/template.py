#
# coding=utf-8
"""template - Template utilities for hubugs"""
# Copyright © 2010-2016  James Rowe <jnrowe@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import datetime
import operator
import os
import sys
import subprocess
import tempfile

import html2text as html2
import jinja2
import misaka

from pygments import highlight as pyg_highlight
from pygments.formatters import get_formatter_by_name
from pygments.lexers import get_lexer_by_name

from . import utils
from .i18n import _


if sys.platform == 'darwin':
    _USER_DATA_DIR = os.path.expanduser('~/Library/Application Support')
else:
    _USER_DATA_DIR = os.path.join(os.environ.get('HOME', '/'), '.local/share')

USER_DATA_DIR = os.environ.get('XDG_DATA_HOME', _USER_DATA_DIR)
SYSTEM_DATA_DIR = os.environ.get('XDG_DATA_DIRS',
                                 '/usr/local/share/:/usr/share/').split(':')
PKG_DATA_DIRS = [os.path.join(USER_DATA_DIR, 'hubugs', 'templates'), ]
for directory in SYSTEM_DATA_DIR:
    PKG_DATA_DIRS.append(os.path.join(directory, 'hubugs', 'templates'))

ENV = jinja2.Environment(loader=jinja2.ChoiceLoader(
    [jinja2.FileSystemLoader(s) for s in PKG_DATA_DIRS]))
ENV.loader.loaders.append(jinja2.PackageLoader('hubugs', 'templates'))


class EmptyMessageError(ValueError):

    """Error to raise when the user provides an empty message."""

    pass


def get_template(group, name):
    """Fetch a Jinja template instance.

    :param str group: Template group identifier
    :param str name: Template name
    :rtype: ``jinja2.environment.Template``
    :return: Jinja template instance
    """
    template_set = utils.get_git_config_val('hubugs.templates', 'default')
    return ENV.get_template('%s/%s/%s' % (template_set, group, name))


def jinja_filter(func):
    """Simple decorator to add a new filter to Jinja environment.

    :param func func: Function to add to Jinja environment
    :rtype: ``func``
    :returns: Unmodified function
    """
    ENV.filters[func.__name__] = func

    return func


@jinja_filter
def colourise(text, formatting):
    """Colourise text using blessings.

    Returns text untouched if colour output is not enabled

    :see: ``blessings``

    :param str text: Text to colourise
    :param str formatting: Formatting to apply to text
    :rtype: ``str``
    :return: Colourised text, when possible
    """
    return getattr(utils.T, formatting.replace(' ', '_'))(text)
# American spelling, just for Brandon Cady ;)
ENV.filters['colorize'] = ENV.filters['colourise']


@jinja_filter
def highlight(text, lexer='diff', formatter='terminal'):
    """Highlight text with pygments.

    Returns text untouched if colour output is not enabled

    :param str text: Text to highlight
    :param str lexer: Jinja lexer to use
    :param str formatter: Jinja formatter to use
    :rtype: ``str``
    :return: Syntax highlighted output, when possible
    """
    if utils.T.is_a_tty:
        lexer = get_lexer_by_name(lexer)
        formatter = get_formatter_by_name(formatter)
        return pyg_highlight(text, lexer, formatter)
    else:
        return text


@jinja_filter
def html2text(html, width=80, ascii_replacements=False):
    """HTML to plain text renderer.

    :param str text: Text to process
    :param int width: Paragraph width
    :param bool ascii_replacements: Use psuedo-ascii replacements for Unicode
    :rtype: ``str``
    :return: Rendered text
    """
    html2.BODY_WIDTH = width
    html2.UNICODE_SNOB = ascii_replacements
    return html2.html2text(html).strip()


@jinja_filter
def markdown(text):
    """Markdown to HTML renderer

    :param str text: Text to process
    :rtype: ``str``
    :return: Rendered HTML
    """
    extensions = misaka.EXT_AUTOLINK | misaka.EXT_FENCED_CODE
    return misaka.html(text, extensions, misaka.HTML_SKIP_HTML)


@jinja_filter
def relative_time(timestamp):
    """Format a relative time.

    Taken from bleeter_.  Duplication is evil, I know.

    :param datetime.datetime timestamp: Event to generate relative timestamp
        against
    :rtype: ``str``
    :return: Human readable date and time offset

    .. _bleeter: http://jnrowe.github.com/bleeter/
    """

    numstr = '. a two three four five six seven eight nine ten'.split()

    matches = [
        60 * 60 * 24 * 365,
        60 * 60 * 24 * 28,
        60 * 60 * 24 * 7,
        60 * 60 * 24,
        60 * 60,
        60,
        1,
    ]
    match_names = ['year', 'month', 'week', 'day', 'hour', 'minute', 'second']

    delta = datetime.datetime.utcnow() - timestamp
    # Switch to delta.total_seconds, if 2.6 support is dropped
    seconds = delta.days * 86400 + delta.seconds
    for scale in matches:
        i = seconds // scale
        if i:
            name = match_names[matches.index(scale)]
            break

    if i == 1 and name in ('year', 'month', 'week'):
        result = 'last %s' % name
    elif i == 1 and name == 'day':
        result = 'yesterday'
    elif i == 1 and name == 'hour':
        result = 'about an hour ago'
    else:
        result = 'about %s %s%s ago' % (i if i > 10 else numstr[i], name,
                                        's' if i > 1 else '')
    return result


def display_bugs(bugs, order, **extras):
    """Display bugs to users.

    :type bugs: ``list` of ``models.Issue``
    :param bugs: Bugs to display
    :param str order: Sorting order for displaying bugs
    :param dict extras: Additional values to pass to templates
    :rtype: ``str``
    :return: Rendered template output
    """
    if not bugs:
        return utils.success(_('No bugs found!'))

    # Match ordering method to bug attribute
    if order == 'updated':
        attr = 'updated_at'
    else:
        attr = order

    bugs = sorted(bugs, key=operator.attrgetter(attr))

    # Default to 80 columns, when stdout is not a tty
    columns = utils.T.width if utils.T.width else 80

    template = get_template('view', 'list.txt')

    max_id = max(i.number for i in bugs)
    id_len = len(str(max_id))
    spacer = ' ' * (id_len - 2)

    return template.render(bugs=bugs, spacer=spacer, id_len=id_len,
                           max_title=columns - id_len - 2, **extras)


def edit_text(edit_type='default', data=None):
    """Edit data with external editor.

    :param str edit_type: Template to use in editor
    :param dict data: Information to pass to template
    :rtype: ``str``
    :return: User supplied text
    :raise EmptyMessageError: No message given
    :raise EmptyMessageError: Message not edited
    """
    template = get_template('edit', '%s.mkd' % edit_type)
    comment_char = utils.get_git_config_val('core.commentchar', '#')
    if not data:
        data = {}
    data['comment_char'] = comment_char

    fd, name = tempfile.mkstemp(prefix='hubugs-', suffix='.mkd')
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(template.render(data))

        orig_mtime = os.path.getmtime(name)
        subprocess.check_call(utils.get_editor() + [name, ])
        new_mtime = os.path.getmtime(name)

        text = ''.join(filter(lambda s: not s.startswith(comment_char),
                              open(name).readlines())).strip()
    finally:
        os.unlink(name)

    if not text:
        raise EmptyMessageError(_('No message given'))
    elif orig_mtime == new_mtime:
        raise EmptyMessageError(_('Message not edited'))

    return text.strip()
