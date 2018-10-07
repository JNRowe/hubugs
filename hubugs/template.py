#
"""template - Template utilities for hubugs."""
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

from typing import Callable, Dict, List, Optional

import click
import html2text as html2
import jinja2
import misaka

from jnrbase import xdg_basedir
from jnrbase.colourise import success
from jnrbase.human_time import human_timestamp
from pygments import highlight as pyg_highlight
from pygments.formatters import get_formatter_by_name
from pygments.lexers import get_lexer_by_name

from . import utils


PKG_DATA_DIRS = [os.path.join(xdg_basedir.user_data('hubugs'), 'templates'), ]
for directory in xdg_basedir.get_data_dirs('hubugs'):
    PKG_DATA_DIRS.append(os.path.join(directory, 'templates'))

ENV = jinja2.Environment(loader=jinja2.ChoiceLoader(
    [jinja2.FileSystemLoader(s) for s in PKG_DATA_DIRS]))
ENV.loader.loaders.append(jinja2.PackageLoader('hubugs', 'templates'))
ENV.filters['relative_time'] = human_timestamp


class EmptyMessageError(ValueError):

    """Error to raise when the user provides an empty message."""

    pass


def get_template(group: str, name: str) -> jinja2.environment.Template:
    """Fetch a Jinja template instance.

    Args:
        group: Template group identifier
        name: Template name

    Returns:
        Jinja template instance
    """
    template_set = utils.get_git_config_val('hubugs.templates', 'default')
    return ENV.get_template('/'.join([template_set, group, name]))


def jinja_filter(func: Callable) -> Callable:
    """Simple decorator to add a new filter to Jinja environment.

    Args:
        func: Function to add to Jinja environment

    Returns:
        Unmodified function
    """
    ENV.filters[func.__name__] = func

    return func


@jinja_filter
def colourise(text: str, fg: Optional[str] = None, bg: Optional[str] = None,
              **kwargs)-> str:
    """Colourise text.

    Returns text untouched if colour output is not enabled

    Args:
        text: Text to colourise
        fg: Foreground colour
        bg: Background colour
        kwargs: Formatting to apply to text

    Returns:
        Colourised text, when possible
    """
    return click.style(text, fg, bg, **kwargs)
# American spelling, just for Brandon Cady ;)
ENV.filters['colorize'] = ENV.filters['colourise']


@jinja_filter
def highlight(text: str, lexer: Optional[str] = 'diff',
              formatter: Optional[str] = 'terminal') -> str:
    """Highlight text with pygments.

    Returns text untouched if colour output is not enabled

    Args:
        text: Text to highlight
        lexer: Jinja lexer to use
        formatter: Jinja formatter to use

    Returns:
        Syntax highlighted output, when possible
    """
    if sys.stdout.isatty():
        lexer = get_lexer_by_name(lexer)
        formatter = get_formatter_by_name(formatter)
        return pyg_highlight(text, lexer, formatter)
    else:
        return text


@jinja_filter
def html2text(html: str, width: Optional[int] = 80,
              ascii_replacements: Optional[bool] = False) -> str:
    """HTML to plain text renderer.

    Args:
        html: Text to process
        width: Paragraph width
        ascii_replacements: Use psuedo-ascii replacements for Unicode

    Returns:
        Rendered text
    """
    html2.BODY_WIDTH = width
    html2.UNICODE_SNOB = ascii_replacements
    return html2.html2text(html).strip()


@jinja_filter
def markdown(text: str) -> str:
    """Markdown to HTML renderer.

    Args:
        text: Text to process

    Returns:
        Rendered HTML
    """
    extensions = misaka.EXT_AUTOLINK | misaka.EXT_FENCED_CODE
    return misaka.html(text, extensions, misaka.HTML_SKIP_HTML)


def display_bugs(bugs: List[Dict[str, str]], order: str, **extras) -> str:
    """Display bugs to users.

    Args:
        bugs: Bugs to display
        order: Sorting order for displaying bugs
        extras: Additional values to pass to templates

    Returns:
        Rendered template output
    """
    if not bugs:
        return success('No bugs found!')

    # Match ordering method to bug attribute
    if order == 'updated':
        attr = 'updated_at'
    else:
        attr = order

    bugs = sorted(bugs, key=operator.attrgetter(attr))

    # Default to 80 columns, when stdout is not a tty
    columns = click.get_terminal_size()[0]

    template = get_template('view', 'list.txt')

    max_id = max(i.number for i in bugs)
    id_len = len(str(max_id))
    spacer = ' ' * (id_len - 2)

    return template.render(bugs=bugs, spacer=spacer, id_len=id_len,
                           max_title=columns - id_len - 2, **extras)


def edit_text(edit_type: Optional[str] = 'default',
              data: Optional[str] = None) -> str:
    """Edit data with external editor.

    Args:
        edit_type: Template to use in editor
        data: Information to pass to template

    Returns:
        User supplied text

    Raises:
        EmptyMessageError: No message given
        EmptyMessageError: Message not edited
    """
    template = get_template('edit', '{}.mkd'.format(edit_type))
    comment_char = utils.get_git_config_val('core.commentchar', '#')
    if not data:
        data = {}
    data['comment_char'] = comment_char

    text = click.edit(template.render(data), require_save=True,
                      extension='.mkd')
    if text:
        text = ''.join(filter(lambda s: not s.startswith(comment_char),
                              text.splitlines())).strip()

    if not text:
        raise EmptyMessageError('No message given')

    return text.strip()
