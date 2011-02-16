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
import operator
import os
import re
import subprocess
import sys

from github2.client import Github


def get_git_config_val(key, allow_fail=False):
    try:
        output = subprocess.check_output(["git", "config", key]).strip()
    except subprocess.CalledProcessError:
        if allow_fail:
            pass
        else:
            raise
    return output


def get_repo():
    data = get_git_config_val("remote.origin.url", True)
    match = re.search(r"github.com[:/](.*).git", data)
    if match:
        return match.groups()[0]
    else:
        raise ValueError("Unknown repository")

def get_term_size():
    return map(int, subprocess.check_output(["stty", "size"]).split())


def display_bugs(bugs):
    if not bugs:
        print "No bugs found!"
        return
    columns = get_term_size()[1]

    max_id = max(i.number for i in bugs)
    id_len = len(str(max_id))

    print "Id %sTitle" % (" " * (id_len - 2))
    fmt_str = "%%%ds %%s" % id_len
    for bug in sorted(bugs, key=operator.attrgetter("number")):
        # Keep title within a single row
        if len(bug.title) > columns - id_len - 2:
            title = "%s…" % bug.title[:columns - id_len - 2]
        else:
            title = bug.title
        print fmt_str % (bug.number, title)

def list_bugs(github, args):
    bugs = github.issues.list(args.repository, args.state)
    display_bugs(bugs)

def search_bugs(github, args):
    bugs = github.issues.search(args.repository, args.term, args.state)
    display_bugs(bugs)


def show_bugs(github, args):
    bugs = [github.issues.show(args.repository, i) for i in args.bugs]
    for bug in bugs:
        print "      Id: %d" % bug.number
        print "   Title: %s" % bug.title
        print "  Labels: %s" % ", ".join(bug.labels)
        print " Created: %s by %s" % (bug.created_at, bug.user)
        print " Updated: %s" % bug.updated_at
        print "   State: %s%s" % (bug.state,
                                 " at %s" % bug.closed_at if bug.closed_at else "")
        print "Comments: %d" % bug.comments
        print "   Votes: %d" % bug.votes
        print
        print bug.body
        if args.full and bug.comments > 0:
            comments = github.issues.comments(args.repository, bug.number)
            for comment in comments:
                print
                print " Created: %s by %s" % (comment.created_at, comment.user)
                print " Updated: %s" % comment.updated_at
                print
                print comment.body


def open_bug(github, args):
    bug = github.issues.open(args.repository, args.title, args.body)
    print "Bug %d opened" % bug.number

def comment_bugs(github, args):
    for bug in args.bugs:
        github.issues.comment(args.repository, bug.number, args.message)


def close_bugs(github, args):
    for bug in args.bugs:
        if args.message:
            github.issues.comment(args.repository, bug.number, args.message)
        github.issues.close(args.repository, bug.number)


def label_bugs(github, args):
    for bug in args.bugs:
        if args.add:
            github.issues.add_label(args.repository, bug.number, args.add)
        if args.remove:
            github.issues.remove_label(args.repository, bug.number, args.remove)


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
    show_parser.add_argument("bugs", nargs="+",
                             help="bug number(s) to operate on")
    show_parser.set_defaults(func=show_bugs)

    open_parser = subparsers.add_parser("open", help="Opening new bugs")
    open_parser.add_argument("title", help="title for the new bug")
    open_parser.add_argument("body", help="body for the new bug", nargs='?')
    open_parser.set_defaults(func=open_bug)

    comment_parser = subparsers.add_parser("comment",
                                           help="Commenting on bugs")
    comment_parser.add_argument("message", help="comment text")
    comment_parser.add_argument("bugs", nargs="+",
                                help="bug number(s) to operate on")
    comment_parser.set_defaults(func=comment_bugs)

    close_parser = subparsers.add_parser("close", help="Closing bugs")
    close_parser.add_argument("message", help="comment text")
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

    if not args.repository:
        args.repository = get_repo()
    elif not "/" in args.repository:
        args.repository = "%s/%s" % (get_git_config_val("github.user"),
                                     args.repository)

    args.func(github, args)

if __name__ == '__main__':
    sys.exit(main())
