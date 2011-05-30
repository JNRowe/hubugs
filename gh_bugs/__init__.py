#
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
__date__ = _version.date
__author__ = "James Rowe <jnrowe@gmail.com>"
__copyright__ = "Copyright (C) 2010-2011  James Rowe <jnrowe@gmail.com>"
__license__ = "GNU General Public License Version 3"
__credits__ = ""
__history__ = "See git repository"

from email.utils import parseaddr

__doc__ += """.

``gh_bugs`` is a very simple client for working with `GitHub's issue tracker`_.

.. _GitHub's issue tracker: http://github.com/blog/411-github-issue-tracker

.. moduleauthor:: `%s <mailto:%s>`__
""" % parseaddr(__author__)

import functools
import sys

import argh

from . import (template, utils)


COMMANDS = []


def command(func):
    "Simple decorator to add function to ``COMMANDS`` list"
    COMMANDS.append(func)

    def decorator(*args, **kwargs):
        return func(*args, **kwargs)

    return functools.update_wrapper(decorator, func)


@command
@argh.alias("list")
@argh.arg("-s", "--state", default="open", choices=["open", "closed", "all"],
          help="state of bugs to list")
@argh.arg("-l", "--label", help="list bugs with specified label",
          metavar="label")
@argh.arg("-o", "--order", default="number",
          choices=["number", "updated", "votes"],
          help="Sort order for listing bugs")
def list_bugs(args):
    "listing bugs"
    if args.label:
        bugs = args.api("list_by_label", args.label)
        if not args.state == "all":
            bugs = filter(lambda x: x.state == args.state, bugs)
    else:
        bugs = []
        states = ["open", "closed"] if args.state == "all" else [args.state, ]
        for state in states:
            bugs.extend(args.api("list", state))
    return template.display_bugs(bugs, args.order, state=args.state)


@command
@argh.arg("-s", "--state", default="open", choices=["open", "closed", "all"],
          help="state of bugs to search")
@argh.arg("-o", "--order", default="number",
          choices=["number", "updated", "votes"],
          help="Sort order for listing bugs")
@argh.arg("term", help="term to search bugs for")
def search(args):
    "searching bugs"
    states = ["open", "closed"] if args.state == "all" else [args.state, ]
    bugs = []
    for state in states:
        bugs.extend(args.api("search", args.term, state))
    return template.display_bugs(bugs, args.order, term=args.term,
                                 state=args.state)


@command
@argh.arg("-f", "--full", default=False, help="show bug including comments")
@argh.arg("-p", "--patch", default=False,
          help="Display patches for pull requests")
@argh.arg("bugs", nargs="+", type=int, help="bug number(s) to operate on")
def show(args):
    "displaying bugs"
    tmpl = template.ENV.get_template("view/issue.txt")
    for bug_no in args.bugs:
        try:
            bug = args.api("show", bug_no)
        except RuntimeError as e:
            if "Issue #%s not found" % bug_no in e.args[0]:
                yield utils.fail("Issue %r not found" % bug_no)
                break
            else:
                raise

        if args.full:
            comments = args.api("comments", bug.number)
        else:
            comments = []
        if args.patch and bug.pull_request_url:
            patch = args._http.request(bug.patch_url)[1]
        else:
            patch = None
        yield tmpl.render(bug=bug, comments=comments, full=True, patch=patch)


@command
@argh.alias("open")
@argh.arg("--stdin", default=False, help="Read message from standard input")
@argh.arg("title", help="title for the new bug", nargs="?")
@argh.arg("body", help="body for the new bug", nargs="?")
@argh.wrap_errors(template.EmptyMessageError)
def open_bug(args):
    "opening new bugs"
    if args.stdin:
        text = sys.stdin.readlines()
    elif not args.title:
        text = template.edit_text("open").splitlines()
    if args.stdin or args.title:
        title = text[0]
        body = "\n".join(text[1:])
    else:
        title = args.title
        body = args.body
    bug = args.api("open", title, body)
    return utils.success("Bug %d opened" % bug.number)


@command
@argh.arg("--stdin", default=False, help="Read message from standard input")
@argh.arg("-m", "--message", help="comment text")
@argh.arg("bugs", nargs="+", type=int, help="bug number(s) to operate on")
@argh.wrap_errors(template.EmptyMessageError)
def comment(args):
    "commenting on bugs"
    if args.stdin:
        message = sys.stdin.read()
    elif args.message:
        message = args.message
    else:
        message = template.edit_text()
    for bug in args.bugs:
        try:
            args.api("comment", bug, message)
        except RuntimeError as e:
            if "Issue #%s not found" % bug in e.args[0]:
                yield utils.fail("Issue %r not found" % bug)
            else:
                raise


@command
@argh.arg("title", help="title for the new bug", nargs="?")
@argh.arg("body", help="body for the new bug", nargs="?")
@argh.arg("bugs", nargs="+", type=int, help="bug number(s) to operate on")
@argh.wrap_errors(template.EmptyMessageError)
def edit(args):
    "editing bugs"
    for bug in args.bugs:
        if not args.title:
            try:
                current = args.api("show", bug)
            except RuntimeError as e:
                if "Issue #%s not found" % bug in e.args[0]:
                    yield utils.fail("Issue %r not found" % bug)
                    continue
                else:
                    raise
            current_data = {"title": current.title, "body": current.body}
            text = template.edit_text("open", current_data).splitlines()
            title = text[0]
            body = "\n".join(text[1:])
        else:
            title = args.title
            body = args.body

        try:
            args.api("edit", bug, title, body)
        except RuntimeError as e:
            if "Issue #%s not found" % bug in e.args[0]:
                yield utils.fail("Issue %r not found" % bug)
            else:
                raise


@command
@argh.arg("-m", "--message", help="comment text")
@argh.arg("bugs", nargs="+", type=int, help="bug number(s) to operate on")
def close(args):
    "closing bugs"
    if not args.message:
        try:
            message = template.edit_text()
        except template.EmptyMessageError:
            # Message isn't required for closing, but it is good practice
            message = None
    else:
        message = args.message
    for bug in args.bugs:
        try:
            if message:
                args.api("comment", bug, message)
            args.api("close", bug)
        except RuntimeError as e:
            if "Issue #%s not found" % bug in e.args[0]:
                yield utils.fail("Issue %r not found" % bug)
            else:
                raise


@command
@argh.arg("-m", "--message", help="comment text")
@argh.arg("bugs", nargs="+", type=int, help="bug number(s) to operate on")
def reopen(args):
    "reopening closed bugs"
    if not args.message:
        try:
            message = template.edit_text()
        except template.EmptyMessageError:
            # Message isn't required for reopening, but it is good practice
            message = None
    else:
        message = args.message
    for bug in args.bugs:
        try:
            if message:
                args.api("comment", bug, message)
            args.api("reopen", bug)
        except RuntimeError as e:
            if "Issue #%s not found" % bug in e.args[0]:
                yield utils.fail("Issue %r not found" % bug)
            else:
                raise


@command
@argh.arg("-a", "--add", action="append", default=[],
          help="add label to issue", metavar="label")
@argh.arg("-r", "--remove", action="append", default=[],
          help="remove label from issue", metavar="label")
@argh.arg("bugs", nargs="+", type=int, help="bug number(s) to operate on")
def label(args):
    "labelling bugs"
    for bug in args.bugs:
        try:
            for label in args.add:
                args.api("add_label", bug, label)
            for label in args.remove:
                args.api("remove_label", bug, label)
        except RuntimeError as e:
            if "Issue #%s not found" % bug in e.args[0]:
                yield utils.fail("Issue %r not found" % bug)
            else:
                raise


def main():
    """Main script"""
    description = __doc__.splitlines()[0].split("-", 1)[1]
    epilog = "Please report bugs to the JNRowe/gh_bugs repository or by " \
             "email to %s" % __author__
    parser = argh.ArghParser(description=description, epilog=epilog,
                             version="%%(prog)s %s" % __version__)
    parser.add_argument("-r", "--repository", action=utils.RepoAction,
                        help="GitHub repository to operate on",
                        metavar="repo")
    parser.add_commands(COMMANDS)
    parser.dispatch(pre_call=utils.set_api)

if __name__ == '__main__':
    main()
