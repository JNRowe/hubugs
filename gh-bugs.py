#! /usr/bin/python -tt
# vim: set sw=4 sts=4 et tw=80 fileencoding=utf-8:
#
"""gh-bugs - Simple client for GitHub issues"""
# Copyright (C) 2010  James Rowe <jnrowe@gmail.com>
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

__version__ = "0.1.0"
__date__ = "2010-10-31"
__author__ = "James Rowe <jnrowe@gmail.com>"
__copyright__ = "Copyright (C) 2010 James Rowe <jnrowe@gmail.com>"
__license__ = "GNU General Public License Version 3"
__credits__ = ""
__history__ = "See git repository"

try:
    from email.utils import parseaddr
except ImportError:  # Python 2.4
    from email.Utils import parseaddr

__doc__ += """.

``gh-bugs`` is a very simple client for working `GitHub's issue tracker`_.

.. _GitHub's issue tracker: http://github.com/blog/411-github-issue-tracker

.. moduleauthor:: `%s <mailto:%s>`__
""" % parseaddr(__author__)

import argparse
import os
import subprocess
import sys

from github2.client import Github


def get_git_config_val(key):
    return subprocess.check_output(["git", "config", key]).strip()


def list_bugs():
    pass


def search_bugs():
    pass


def show_bugs():
    pass


def open_bug():
    pass


def comment_bugs():
    pass


def close_bugs():
    pass


def label_bugs():
    pass

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
                             choices=["open", "closed"],
                             help="state of bugs to list")
    list_parser.add_argument("-l", "--label",
                             help="list bugs with specified label",
                             metavar="label")
    list_parser.set_defaults(func=list_bugs)

    search_parser = subparsers.add_parser("search", help="Searching bugs")
    search_parser.add_argument("-s", "--state", default="open",
                               choices=["open", "closed"],
                               help="state of bugs to search")
    search_parser.add_argument("term", help="term to search bugs for")
    search_parser.set_defaults(func=search_bugs)

    show_parser = subparsers.add_parser("show", help="Displaying bugs")
    show_parser.add_argument("-f", "--full", action="store_true",
                             help="show bug including comments")
    show_parser.add_argument("bug", nargs="+",
                             help="bug number(s) to operate on")
    show_parser.set_defaults(func=show_bugs)

    open_parser = subparsers.add_parser("open", help="Opening new bugs")
    open_parser.add_argument("title", help="title for the new bug")
    open_parser.add_argument("body", help="body for the new bug", nargs='?')
    open_parser.set_defaults(func=open_bug)

    comment_parser = subparsers.add_parser("comment",
                                           help="Commenting on bugs")
    comment_parser.add_argument("message", help="comment text")
    comment_parser.add_argument("bug", nargs="+",
                                help="bug number(s) to operate on")
    comment_parser.set_defaults(func=comment_bugs)

    close_parser = subparsers.add_parser("close", help="Closing bugs")
    close_parser.add_argument("message", help="comment text")
    close_parser.add_argument("bug", nargs="+",
                              help="bug number(s) to operate on")
    close_parser.set_defaults(func=close_bugs)

    label_parser = subparsers.add_parser("label", help="Labelling bugs")
    label_parser.add_argument("-a", "--add", help="add label to issue",
                              metavar="label")
    label_parser.add_argument("-r", "--remove", help="remove label from issue",
                              metavar="label")
    label_parser.add_argument("bug", nargs="+",
                              help="bug number(s) to operate on")
    label_parser.set_defaults(func=label_bugs)

    args = parser.parse_args()
    return args


def main():
    args = process_command_line()

    user = get_git_config_val("github.user")
    token = get_git_config_val("github.token")

    xdg_cache_dir = os.getenv("XDG_CACHE_HOME",
                              os.path.join(os.getenv("HOME", "/"), ".cache"))
    cache_dir = os.path.join(xdg_cache_dir, "gh-bugs")

    github = Github(username=user, api_token=token, cache=cache_dir)

if __name__ == '__main__':
    sys.exit(main())
