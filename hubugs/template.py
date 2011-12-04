#
# coding=utf-8
"""template - Template utilities for hubugs"""
# Copyright (C) 2010-2011  James Rowe <jnrowe@gmail.com>
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
import re
import sys
import subprocess
import tempfile

import html2text as html2
import jinja2
import markdown2

from dateutil import tz
from pygments import highlight as pyg_highlight
from pygments.formatters import get_formatter_by_name
from pygments.lexers import get_lexer_by_name

from . import utils


USER_DATA_DIR = os.environ.get("XDG_DATA_HOME",
                               os.path.join(os.environ.get("HOME", "/"),
                                            ".local"))
SYSTEM_DATA_DIR = os.environ.get("XDG_DATA_DIRS",
                                 "/usr/local/share/:/usr/share/").split(":")
PKG_DATA_DIRS = [os.path.join(USER_DATA_DIR, "hubugs", "templates"), ]
for directory in SYSTEM_DATA_DIR:
    PKG_DATA_DIRS.append(os.path.join(directory, "hubugs", "templates"))

ENV = jinja2.Environment(loader=jinja2.ChoiceLoader(
    [jinja2.FileSystemLoader(s) for s in PKG_DATA_DIRS]))
ENV.loader.loaders.append(jinja2.PackageLoader("hubugs", "templates"))


class EmptyMessageError(ValueError):
    """Error to raise when the user provides an empty message"""
    pass


def get_template(group, name):
    """Fetch a Jinja template instance

    :param str group: Template group indentifier
    :param str name: Template name
    :rtype: jinja2.environment.Template
    :return: Jinja template instance
    """
    template_set = utils.get_git_config_val('hubugs.templates', 'default')
    return ENV.get_template("%s/%s/%s" % (template_set, group, name))


def jinja_filter(func):
    "Simple decorator to add function to Jinja filters"
    ENV.filters[func.__name__] = func

    return func


@jinja_filter
def colourise(text, *args, **kwargs):
    """Colourise text with termcolor.

    Returns text untouched if colour output is not enabled

    :see: ``termcolor.colored``

    :rtype: ``str``
    :return: Colourised text, when possible
    """
    if utils.colored and sys.stdout.isatty():
        return utils.colored(text, *args, **kwargs)
    else:
        return text
# American spelling, just for Brandon Cady ;)
ENV.filters["colorize"] = ENV.filters["colourise"]


@jinja_filter
def highlight(text, lexer="diff", formatter="terminal"):
    """Highlight text with pygments

    Returns text untouched if colour output is not enabled

    :param str text: Text to highlight
    :param str lexer: Jinja lexer to use
    :param str formatter:
    :rtype: ``str``
    :return: Syntax highlighted output, when possible
    """
    if utils.colored and sys.stdout.isatty():
        lexer = get_lexer_by_name(lexer)
        formatter = get_formatter_by_name(formatter)
        return pyg_highlight(text, lexer, formatter)
    else:
        return text


@jinja_filter
def html2text(html, width=80, ascii_replacements=False):
    """HTML to plain text renderer

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
def markdown(text, tab_width=markdown2.DEFAULT_TAB_WIDTH):
    """Markdown to HTML renderer

    :param str text: Text to process
    :param int tab_width: Indentation width
    :rtype: ``str``
    :return: Rendered HTML
    """
    return markdown2.markdown(text, tab_width=tab_width)


@jinja_filter
def relative_time(timestamp):
    """Format a relative time

    Taken from bleeter_.  Duplication is evil, I know.

    :param datetime.datetime timestamp: Event to generate relative timestamp
        against
    :rtype: ``str``
    :return: Human readable date and time offset

    .. _bleeter: http://jnrowe.github.com/bleeter/
    """

    numstr = ". a two three four five six seven eight nine ten".split()

    matches = [
        60 * 60 * 24 * 365,
        60 * 60 * 24 * 28,
        60 * 60 * 24 * 7,
        60 * 60 * 24,
        60 * 60,
        60,
        1,
    ]
    match_names = ["year", "month", "week", "day", "hour", "minute", "second"]

    delta = datetime.datetime.utcnow().replace(tzinfo=tz.tzutc()) - timestamp
    # Switch to delta.total_seconds, if 2.6 support is dropped
    seconds = delta.days * 86400 + delta.seconds
    for scale in matches:
        i = seconds // scale
        if i:
            name = match_names[matches.index(scale)]
            break

    if i == 1 and name in ("year", "month", "week"):
        result = "last %s" % name
    elif i == 1 and name == "day":
        result = "yesterday"
    elif i == 1 and name == "hour":
        result = "about an hour ago"
    else:
        result = "about %s %s%s ago" % (i if i > 10 else numstr[i], name,
                                        "s" if i > 1 else "")
    return result


@jinja_filter
def term_markdown(text):
    """Basic Markdown text-based renderer

    Formats headings, horizontal rules and emphasis.

    :param str text: Text to process
    :rtype: ``str``
    :return: Rendered text with terminal control sequences
    """
    if not utils.colored or not sys.stdout.isatty():
        return text
    # For uniform line ending split and rejoin, this saves having to handle \r
    # and \r\n
    text = "\n".join(text.splitlines())

    # Compile these REs for Python 2.6 compatibility, as flags isn't supported
    # as a re.sub keyword argument until 2.7.  The others can take advantage of
    # the implicit caching.
    headings_re = re.compile(r"^#+ +(.*)$", re.MULTILINE)
    rules_re = re.compile(r"^(([*-] *){3,})$", re.MULTILINE)
    bullets_re = re.compile(r"^( {0,4})[*+-] ", re.MULTILINE)
    quotes_re = re.compile(r"^> .*$", re.MULTILINE)

    text = headings_re.sub(lambda s: utils.colored(s.groups()[0], attrs=["underline"]),
                           text)
    text = rules_re.sub(lambda s: utils.colored(s.groups()[0], "green"),
                        text)
    text = re.sub(r'([\*_]{2})([^ \*]+)\1',
                  lambda s: utils.colored(s.groups()[1], attrs=["underline"]),
                  text)
    text = quotes_re.sub(lambda s: utils.colored(s.group(), attrs=["reverse"]),
                         text)
    text = re.sub(r'([\*_])([^ \*]+)\1',
                  lambda s: utils.colored(s.groups()[1], attrs=["bold"]), text)
    if sys.stdout.encoding == "UTF-8":
        text = bullets_re.sub(u"\\1• ", text)

    return text


def display_bugs(bugs, order, **extras):
    """Display bugs to users

    :type bugs: ``list` of ``github2.issues.Issue``
    :param bugs: Bugs to display
    :param str order: Sorting order for displaying bugs
    :param dict extras: Additional values to pass to templates
    """
    if not bugs:
        return utils.success("No bugs found!")

    # Match ordering method to bug attribute
    if order == "updated":
        attr = "updated_at"
    else:
        attr = order

    bugs = sorted(bugs, key=operator.attrgetter(attr))

    columns = utils.get_term_size().columns

    template = get_template('view', 'list.txt')

    max_id = max(i.number for i in bugs)
    id_len = len(str(max_id))
    spacer = " " * (id_len - 2)

    return template.render(bugs=bugs, spacer=spacer, id_len=id_len,
                           max_title=columns - id_len - 2, **extras)


def edit_text(edit_type="default", data=None):
    """Edit data with external editor

    :param str edit_type: Template to use in editor
    :param dict data: Information to pass to template
    :rtype: ``str``
    :return: User supplied text
    :raise EmptyMessageError: No message given
    """
    template = get_template('edit', '%s.mkd' % edit_type)
    with tempfile.NamedTemporaryFile(suffix=".mkd") as temp:
        temp.write(template.render(data if data else {}))
        temp.flush()

        subprocess.check_call([utils.get_editor(), temp.name])

        temp.seek(0)
        text = "".join(filter(lambda s: not s.startswith("#"),
                              temp.readlines())).strip()

    if not text:
        raise EmptyMessageError("No message given")

    return text.strip()
