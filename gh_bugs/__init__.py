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

import argh

from . import (template, utils)


@argh.alias("list")
@argh.arg("-s", "--state", default="open", choices=["open", "closed", "all"],
          help="state of bugs to list")
# Currently not supported in python-github2, see
# https://github.com/ask/python-github2/pull/32
#@argh.arg("-l", "--label", help="list bugs with specified label",
#          metavar="label")
@argh.arg("-o", "--order", default="number",
          choices=["number", "priority", "updated", "votes"],
          help="Sort order for listing bugs")
def list_bugs(args):
    "listing bugs"
    github = utils.get_github_api()
    states = ["open", "closed"] if args.state == "all" else [args.state, ]
    bugs = []
    for state in states:
        bugs.extend(github.issues.list(args.repository, state))
    return template.display_bugs(bugs, args.order)


@argh.arg("-s", "--state", default="open", choices=["open", "closed", "all"],
          help="state of bugs to search")
@argh.arg("-o", "--order", default="number",
          choices=["number", "priority", "updated", "votes"],
          help="Sort order for listing bugs")
@argh.arg("term", help="term to search bugs for")
def search(args):
    "searching bugs"
    github = utils.get_github_api()
    states = ["open", "closed"] if args.state == "all" else [args.state, ]
    bugs = []
    for state in states:
        bugs.extend(github.issues.search(args.repository, args.term, state))
    return template.display_bugs(bugs, args.order)


@argh.arg("-f", "--full", default=False, help="show bug including comments")
@argh.arg("bugs", nargs="+", type=int, help="bug number(s) to operate on")
def show(args):
    "displaying bugs"
    github = utils.get_github_api()
    tmpl = template.ENV.get_template("view/issue.txt")
    for bug_no in args.bugs:
        try:
            bug = github.issues.show(args.repository, bug_no)
        except RuntimeError as e:
            if "Issue #%s not found" % bug_no in e.args[0]:
                yield utils.fail("Issue %r not found" % bug_no)
            else:
                raise

        if args.full:
            comments = github.issues.comments(args.repository, bug.number)
        else:
            comments = []
        yield tmpl.render(bug=bug, comments=comments, full=True)


@argh.alias("open")
@argh.arg("title", help="title for the new bug", nargs="?")
@argh.arg("body", help="body for the new bug", nargs="?")
@argh.wrap_errors(template.EmptyMessageError)
def open_bug(args):
    "opening new bugs"
    github = utils.get_github_api()
    if not args.title:
        text = template.edit_text("open").splitlines()
        title = text[0]
        body = "\n".join(text[1:])
    else:
        title = args.title
        body = args.body
    bug = github.issues.open(args.repository, title, body)
    return utils.success("Bug %d opened" % bug.number)


@argh.arg("-m", "--message", help="comment text")
@argh.arg("bugs", nargs="+", type=int, help="bug number(s) to operate on")
@argh.wrap_errors(template.EmptyMessageError)
def comment(args):
    "commenting on bugs"
    github = utils.get_github_api()
    if not args.message:
        message = template.edit_text()
    else:
        message = args.message
    for bug in args.bugs:
        try:
            github.issues.comment(args.repository, bug, message)
        except RuntimeError as e:
            if "Issue #%s not found" % bug in e.args[0]:
                yield utils.fail("Issue %r not found" % bug)
            else:
                raise


@argh.arg("title", help="title for the new bug", nargs="?")
@argh.arg("body", help="body for the new bug", nargs="?")
@argh.arg("bugs", nargs="+", type=int, help="bug number(s) to operate on")
@argh.wrap_errors(template.EmptyMessageError)
def edit(args):
    "editing bugs"
    github = utils.get_github_api()
    for bug in args.bugs:
        if not args.title:
            try:
                current = github.issues.show(args.repository, bug)
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
            github.issues.edit(args.repository, bug, title, body)
        except RuntimeError as e:
            if "Issue #%s not found" % bug in e.args[0]:
                yield utils.fail("Issue %r not found" % bug)
            else:
                raise


@argh.arg("-m", "--message", help="comment text")
@argh.arg("bugs", nargs="+", type=int, help="bug number(s) to operate on")
def close(args):
    "closing bugs"
    github = utils.get_github_api()
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
                github.issues.comment(args.repository, bug, message)
            github.issues.close(args.repository, bug)
        except RuntimeError as e:
            if "Issue #%s not found" % bug in e.args[0]:
                yield utils.fail("Issue %r not found" % bug)
            else:
                raise


@argh.arg("-m", "--message", help="comment text")
@argh.arg("bugs", nargs="+", type=int, help="bug number(s) to operate on")
def reopen(args):
    "reopening closed bugs"
    github = utils.get_github_api()
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
                github.issues.comment(args.repository, bug, message)
            github.issues.reopen(args.repository, bug)
        except RuntimeError as e:
            if "Issue #%s not found" % bug in e.args[0]:
                yield utils.fail("Issue %r not found" % bug)
            else:
                raise


@argh.arg("-a", "--add", action="append", default=[],
          help="add label to issue", metavar="label")
@argh.arg("-r", "--remove", action="append", default=[],
          help="remove label from issue", metavar="label")
@argh.arg("bugs", nargs="+", type=int, help="bug number(s) to operate on")
def label(args):
    "labelling bugs"
    github = utils.get_github_api()
    for bug in args.bugs:
        try:
            for label in args.add:
                github.issues.add_label(args.repository, bug, label)
            for label in args.remove:
                github.issues.remove_label(args.repository, bug, label)
        except RuntimeError as e:
            if "Issue #%s not found" % bug in e.args[0]:
                yield utils.fail("Issue %r not found" % bug)
            else:
                raise


def main():
    """Main script"""
    parser = argh.ArghParser(description=__doc__.splitlines()[0],
                             epilog="Please report bugs to the JNRowe/gh_bugs" \
                                    " repository or by email to %s" % __author__,
                             version="%%(prog)s %s" % __version__)
    parser.add_argument("-r", "--repository", action=utils.RepoAction,
                        default=utils.get_repo(),
                        help="GitHub repository to operate on",
                        metavar="repo")
    parser.add_commands([list_bugs, search, show, open_bug, comment, edit,
                         close, reopen, label])
    parser.dispatch()

if __name__ == '__main__':
    main()
