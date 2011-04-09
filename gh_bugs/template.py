#
# coding=utf-8
"""template_utils - Template utilities for gh_bugs"""
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
import functools
import operator
import os
import re
import sys
import subprocess
import tempfile

import jinja2

from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import DiffLexer

from . import utils


USER_DATA_DIR = os.environ.get("XDG_DATA_HOME",
                               os.path.join(os.environ.get("HOME", "/"),
                                            ".local"))
SYSTEM_DATA_DIR = os.environ.get("XDG_DATA_DIRS",
                                 "/usr/local/share/:/usr/share/").split(":")
PKG_DATA_DIRS = [os.path.join(USER_DATA_DIR, "gh_bugs", "templates"), ]
for directory in SYSTEM_DATA_DIR:
    PKG_DATA_DIRS.append(os.path.join(directory, "gh_bugs", "templates"))

ENV = jinja2.Environment(loader=jinja2.ChoiceLoader(
    [jinja2.FileSystemLoader(s) for s in PKG_DATA_DIRS]))
ENV.loader.loaders.append(jinja2.PackageLoader("gh_bugs", "templates"))
if utils.colored and sys.stdout.isatty():
    ENV.filters["colourise"] = utils.colored
    # American spelling, just for Brandon Cady ;)
    ENV.filters["colorize"] = ENV.filters["colourise"]
    ENV.filters["highlight"] = lambda string: highlight(string, DiffLexer(),
                                                        TerminalFormatter())
else:
    ENV.filters["colourise"] = lambda string, *args, **kwargs: string
    ENV.filters["colorize"] = ENV.filters["colourise"]
    ENV.filters["highlight"] = lambda string: string


class EmptyMessageError(ValueError):
     pass


def jinja_filter(func):
    "Simple decorator to add function to Jinja filters"
    ENV.filters[func.__name__] = func
    def decorator(*args):
        return func(*args)
    return functools.update_wrapper(decorator, func)


@jinja_filter
def relative_time(timestamp):
    """Format a relative time

    Taken from bleeter_.  Duplication is evil, I know.

    :type timestamp: ``datetime.datetime``
    :param timestamp: Event to generate relative timestamp against
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

    delta = datetime.datetime.now(utils.UTC()) - timestamp
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

    :type text: ``str``
    :param text: Text to process
    :rtype: ``str``
    :return: Rendered text with terminal control sequences
    """
    if utils.colored and sys.stdout.isatty():
        # For uniform line ending split and rejoin, this saves having to handle \r and \r\n
        text = "\n".join(text.splitlines())
        text = re.sub(r"^#+ +(.*)$",
                      lambda s: utils.colored(s.groups()[0], attrs=["underline"]),
                      text, flags=re.MULTILINE)
        text = re.sub(r"^(([*-] *){3,})$",
                      lambda s: utils.colored(s.groups()[0], "green"),
                      text, flags=re.MULTILINE)
        text = re.sub(r'([\*_]{2})([^ \*]+)\1',
                      lambda s: utils.colored(s.groups()[1], attrs=["underline"]),
                      text)
        text = re.sub(r'([\*_])([^ \*]+)\1',
                      lambda s: utils.colored(s.groups()[1], attrs=["bold"]), text)
        if sys.stdout.encoding == "UTF-8":
            text = re.sub(r"^( {0,4})[*+-] ", u"\\1• ", text,
                          flags=re.MULTILINE)

    return text

def display_bugs(bugs, order):
    """Display bugs to users

    :type bugs: ``list` of ``github2.issues.Issue``
    :param bugs: Bugs to display
    :type order: ``str``
    :param order: Sorting order for displaying bugs
    """
    if not bugs:
        return utils.success("No bugs found!")

    # Match ordering method to bug attribute
    if order == "priority":
        attr = "position"
    elif order == "updated":
        attr = "updated_at"
    else:
        attr = order

    bugs = sorted(bugs, key=operator.attrgetter(attr))

    columns = utils.get_term_size()[1]

    template = ENV.get_template("view/list.txt")

    max_id = max(i.number for i in bugs)
    id_len = len(str(max_id))
    spacer = " " * (id_len - 2)

    return template.render(bugs=bugs, spacer=spacer, id_len=id_len,
                           max_title=columns - id_len - 2)

def edit_text(edit_type="default", data=None):
    """Edit data with external editor

    :type edit_type: ``str``
    :param edit_type: Template to use in editor
    :type data: ``dict``
    :param data: Information to pass to template
    :rtype: ``str``
    :return: User supplied text
    :raise EmptyMessageError: No message given
    """
    template = ENV.get_template("edit/%s.mkd" % edit_type)
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
