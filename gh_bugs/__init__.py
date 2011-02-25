#! /usr/bin/python -tt
# coding=utf-8
"""gh_bugs - Simple client for GitHub issues"""
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

from . import _version


__version__ = _version.dotted
__date__ = "2010-10-31"
__author__ = "James Rowe <jnrowe@gmail.com>"
__copyright__ = "Copyright (C) 2010-2011  James Rowe <jnrowe@gmail.com>"
__license__ = "GNU General Public License Version 3"
__credits__ = ""
__history__ = "See git repository"

from email.utils import parseaddr

__doc__ += """.

``gh_bugs`` is a very simple client for working `GitHub's issue tracker`_.

.. _GitHub's issue tracker: http://github.com/blog/411-github-issue-tracker

.. moduleauthor:: `%s <mailto:%s>`__
""" % parseaddr(__author__)

import argparse
import datetime
import operator
import os
import re
import subprocess
import sys
import tempfile

import jinja2

from github2.client import Github

try:
    from termcolor import colored
except ImportError:  # pragma: no cover
    colored = None  # pylint: disable-msg=C0103

# Select colours if terminal is a tty
# pylint: disable-msg=C0103
if colored and sys.stdout.isatty():
    success = lambda s: colored(s, "green")
    fail = lambda s: colored(s, "red")
    warn = lambda s: colored(s, "yellow")
else:  # pragma: no cover
    success = fail = warn = str
# pylint: enable-msg=C0103


ENV = jinja2.Environment(loader=jinja2.PackageLoader("gh_bugs", "templates/"))
ENV.filters["relative_time"] = lambda timestamp: relative_time(timestamp)
ENV.filters["colourise"] = colored if colored else lambda string, colour: string


class UTC(datetime.tzinfo):
    """UTC"""

    def utcoffset(self, timestamp):
        return datetime.timedelta(0)

    def tzname(self, timestamp):
        return "UTC"

    def dst(self, timestamp):
        return datetime.timedelta(0)


def edit_text(edit_type="default"):
    """Edit data with external editor

    :type edit_type: ``str``
    :param edit_type: Template to use in editor
    :rtype: ``str``
    :return: User supplied text
    :raise ValueError: No message given
    """
    template = ENV.get_template("edit/%s.mkd" % edit_type)
    with tempfile.NamedTemporaryFile(suffix=".mkd") as temp:
        temp.write(template.render())
        temp.flush()

        subprocess.check_call([get_editor(), temp.name])

        temp.seek(0)
        text = "".join(filter(lambda s: not s.startswith("#"),
                              temp.readlines())).strip()

    if not text:
        raise ValueError("No message given")

    return text.strip()


def get_git_config_val(key, allow_fail=False):
    """Fetch a git configuration value

    :type key: ``str``
    :param key: Configuration value to fetch
    :type allow_fail: ``bool``
    :param allow_fail: Ignore errors
    :raise subprocess.CalledProcessError: If ``allow_fail`` is False, and
        command returns non-zero exit code
    """
    try:
        output = subprocess.check_output(["git", "config", key]).strip()
    except subprocess.CalledProcessError:
        if allow_fail:
            output = None
        else:
            raise
    return output


def get_editor():
    """Choose a suitable editor

    This follows the method defined in :manpage:`git-var(1)`

    :rtype: ``str``
    :return: Users chosen editor, or ``vi`` if not set"""
    # Match git for editor preferences
    editor = os.getenv("GIT_EDITOR")
    if not editor:
        editor = get_git_config_val("core.editor", allow_fail=True)
        if not editor:
            editor = os.getenv("VISUAL", os.getenv("EDITOR", "vi"))
    return editor


def get_repo():
    """Identify the current GitHub repository

    :rtype: ``str``
    :return: GitHub repository user and name
    :raise ValueError: If GitHub repository can't be ascertained
    """
    data = get_git_config_val("remote.origin.url", True)
    match = re.search(r"github.com[:/](.*).git", data)
    if match:
        return match.groups()[0]
    else:
        raise ValueError("Unknown repository")


def get_term_size():
    """Fetch the current terminal size

    :rtype: ``list`` of ``int``
    :return: Number of columns and lines in current terminal
    """
    return map(int, subprocess.check_output(["stty", "size"]).split())


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

    delta = datetime.datetime.now(UTC()) - timestamp
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


def display_bugs(bugs):
    """Display bugs to users

    :type bugs: ``list` of ``github2.issues.Issue``
    :param bugs: Bugs to display
    """
    if not bugs:
        print fail("No bugs found!")
        return
    columns = get_term_size()[1]

    template = ENV.get_template("view/list.txt")

    max_id = max(i.number for i in bugs)
    id_len = len(str(max_id))
    spacer = " " * (id_len - 2)

    print template.render(bugs=bugs, spacer=spacer, id_len=id_len,
                          max_title=columns - id_len - 2)


def list_bugs(github, args):
    """Command function to list bugs

    :type args: ``argparse.Namespace``
    :param args: Processed command line options.  ``repository`` and ``state``
        are used
    :type github: ``github2.client.Github``
    :param github: Authenticated GitHub client instance
    """
    states = ["open", "closed"] if args.state == "all" else [args.state, ]
    bugs = []
    for state in states:
        bugs.extend(github.issues.list(args.repository, state))
    display_bugs(bugs)


def search_bugs(github, args):
    """Command function to search bugs

    :type args: ``argparse.Namespace``
    :param args: Processed command line options.  ``repository``, ``term`` and
        ``state`` are used
    :type github: ``github2.client.Github``
    :param github: Authenticated GitHub client instance
    """
    states = ["open", "closed"] if args.state == "all" else [args.state, ]
    bugs = []
    for state in states:
        bugs.extend(github.issues.search(args.repository, args.term, state))
    display_bugs(bugs)


def show_bugs(github, args):
    """Command function to show bug(s) in detail

    :type args: ``argparse.Namespace``
    :param args: Processed command line options.  ``repository``, ``bugs`` and
        ``full`` are used
    :type github: ``github2.client.Github``
    :param github: Authenticated GitHub client instance
    """
    bugs = [github.issues.show(args.repository, i) for i in args.bugs]

    template = ENV.get_template("view/issue.txt")
    for bug in bugs:
        if args.full:
            comments = github.issues.comments(args.repository, bug.number)
        else:
            comments = []
        print template.render(bug=bug, comments=comments, full=True)


def open_bug(github, args):
    """Command function to open a bug

    :type args: ``argparse.Namespace``
    :param args: Processed command line options.  ``repository``, ``title`` and
        ``body`` are used
    :type github: ``github2.client.Github``
    :param github: Authenticated GitHub client instance
    """
    if not args.title:
        text = edit_text("open").splitlines()
        title = text[0]
        body = "\n".join(text[1:])
    else:
        title = args.title
        body = args.body
    bug = github.issues.open(args.repository, title, body)
    print success("Bug %d opened" % bug.number)


def comment_bugs(github, args):
    """Command function to comment on bug(s)

    :type args: ``argparse.Namespace``
    :param args: Processed command line options.  ``repository``, ``message``
        and ``bugs`` are used
    :type github: ``github2.client.Github``
    :param github: Authenticated GitHub client instance
    """
    if not args.message:
        message = edit_text()
    else:
        message = args.message
    for bug in args.bugs:
        github.issues.comment(args.repository, bug, message)


def close_bugs(github, args):
    """Command function to close bug(s)

    :type args: ``argparse.Namespace``
    :param args: Processed command line options.  ``repository``, ``message``
        and ``bugs`` are used
    :type github: ``github2.client.Github``
    :param github: Authenticated GitHub client instance
    """
    if not args.message:
        try:
            message = edit_text()
        except ValueError:
            # Message isn't required for closing, but it is good practice
            message = None
    else:
        message = args.message
    for bug in args.bugs:
        if message:
            github.issues.comment(args.repository, bug, message)
        github.issues.close(args.repository, bug)


def label_bugs(github, args):
    """Command function to list bugs

    :type args: ``argparse.Namespace``
    :param args: Processed command line options. ``repository``, ``bugs``,
        ``add`` and ``remove`` are used
    :type github: ``github2.client.Github``
    :param github: Authenticated GitHub client instance
    """
    for bug in args.bugs:
        if args.add:
            github.issues.add_label(args.repository, bug, args.add)
        if args.remove:
            github.issues.remove_label(args.repository, bug, args.remove)


def process_command_line():
    """Process command line options

    :rtype: ``'argparse.Namespace'``
    :return: Parsed options and arguments
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version',
                        version='%%(prog)s %s' % __version__)

    parser.add_argument("-r", "--repository",
                        help="GitHub repository to operate on",
                        metavar="repo")

    subparsers = parser.add_subparsers()

    list_parser = subparsers.add_parser("list", help="Listing bugs")
    list_parser.add_argument("-s", "--state", default="open",
                             choices=["open", "closed", "all"],
                             help="state of bugs to list")
    list_parser.add_argument("-l", "--label",
                             help="list bugs with specified label",
                             metavar="label")
    list_parser.set_defaults(func=list_bugs)

    search_parser = subparsers.add_parser("search", help="Searching bugs")
    search_parser.add_argument("-s", "--state", default="open",
                               choices=["open", "closed", "all"],
                               help="state of bugs to search")
    search_parser.add_argument("term", help="term to search bugs for")
    search_parser.set_defaults(func=search_bugs)

    show_parser = subparsers.add_parser("show", help="Displaying bugs")
    show_parser.add_argument("-f", "--full", action="store_true",
                             help="show bug including comments")
    show_parser.add_argument("bugs", nargs="+",
                             help="bug number(s) to operate on")
    show_parser.set_defaults(func=show_bugs)

    open_parser = subparsers.add_parser("open", help="Opening new bugs")
    open_parser.add_argument("title", help="title for the new bug", nargs="?")
    open_parser.add_argument("body", help="body for the new bug", nargs="?")
    open_parser.set_defaults(func=open_bug)

    comment_parser = subparsers.add_parser("comment",
                                           help="Commenting on bugs")
    comment_parser.add_argument("-m", "--message", help="comment text")
    comment_parser.add_argument("bugs", nargs="+",
                                help="bug number(s) to operate on")
    comment_parser.set_defaults(func=comment_bugs)

    close_parser = subparsers.add_parser("close", help="Closing bugs")
    close_parser.add_argument("-m", "--message", help="comment text")
    close_parser.add_argument("bugs", nargs="+",
                              help="bug number(s) to operate on")
    close_parser.set_defaults(func=close_bugs)

    label_parser = subparsers.add_parser("label", help="Labelling bugs")
    label_parser.add_argument("-a", "--add", help="add label to issue",
                              metavar="label")
    label_parser.add_argument("-r", "--remove", help="remove label from issue",
                              metavar="label")
    label_parser.add_argument("bugs", nargs="+",
                              help="bug number(s) to operate on")
    label_parser.set_defaults(func=label_bugs)

    return parser.parse_args()


def main():
    """Main script

    :rtype: ``int``
    :return: Exit code
    """
    args = process_command_line()

    user = get_git_config_val("github.user")
    token = get_git_config_val("github.token")

    xdg_cache_dir = os.getenv("XDG_CACHE_HOME",
                              os.path.join(os.getenv("HOME", "/"), ".cache"))
    cache_dir = os.path.join(xdg_cache_dir, "gh_bugs")

    github = Github(username=user, api_token=token, cache=cache_dir)

    if not args.repository:
        args.repository = get_repo()
    elif not "/" in args.repository:
        args.repository = "%s/%s" % (get_git_config_val("github.user"),
                                     args.repository)

    return args.func(github, args)

if __name__ == '__main__':
    sys.exit(main())
