#
# coding=utf-8
"""hubugs - Simple client for GitHub issues"""
# Copyright (C) 2010-2012  James Rowe <jnrowe@gmail.com>
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
__copyright__ = "Copyright (C) 2010-2012  James Rowe <jnrowe@gmail.com>"
__license__ = "GNU General Public License Version 3"
__credits__ = ""
__history__ = "See git repository"

from email.utils import parseaddr

__doc__ += """.

``hubugs`` is a very simple client for working with `GitHub's issue tracker`_.

.. _GitHub's issue tracker: http://github.com/blog/411-github-issue-tracker

.. moduleauthor:: `%s <mailto:%s>`__
""" % parseaddr(__author__)

import atexit
import logging
import sys
import webbrowser

import argh
import httplib2


logging.basicConfig(level=logging.ERROR,
                    format="%(asctime)s - %(message)s",
                    datefmt="%Y-%m-%dT%H:%M:%S")
atexit.register(logging.shutdown)


from github2.request import (HttpError, charset_from_headers)

from . import (template, utils)


COMMANDS = []


def command(func):
    """Simple decorator to add function to ``COMMANDS`` list

    The purpose of this decorator is to make the definition of commands simpler
    by reducing duplication, it is purely a convenience.

    :param func func: Function to wrap
    :rtype: func
    :returns: Original function
    """
    COMMANDS.append(func)
    return func


# Convenience wrappers for defining command arguments
# pylint: disable-msg=C0103
bugs_arg = argh.arg("bugs", nargs="+", type=int,
                    help="bug number(s) to operate on")

message_arg = argh.arg("-m", "--message", help="comment text")

order_arg = argh.arg("-o", "--order", default="number",
                     choices=["number", "updated", "votes"],
                     help="sort order for listing bugs")

states_arg = argh.arg("-s", "--state", default="open",
                      choices=["open", "closed", "all"],
                      help="state of bugs to operate on")

stdin_arg = argh.arg("--stdin", default=False,
                     help="read message from standard input")

title_arg = argh.arg("title", help="title for the new bug", nargs="?")
body_arg = argh.arg("body", help="body for the new bug", nargs="?")

label_add_arg = argh.arg("-a", "--add", action="append", default=[],
                         help="add label to issue", metavar="label")
label_remove_arg = argh.arg("-r", "--remove", action="append", default=[],
                            help="remove label from issue", metavar="label")
# pylint: enable-msg=C0103


@command
@argh.alias("list")
@states_arg
@argh.arg("-l", "--label", help="list bugs with specified label",
          metavar="label")
@order_arg
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
@states_arg
@order_arg
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
          help="display patches for pull requests")
@argh.arg("-b", "--browse", default=False, help="open bug in web browser")
@bugs_arg
def show(args):
    "displaying bugs"
    tmpl = template.get_template('view', '/issue.txt')
    for bug_no in args.bugs:
        if args.browse:
            webbrowser.open_new_tab("https://github.com/%s/issues/%d"
                                    % (args.project, bug_no))
            continue
        try:
            bug = args.api("show", bug_no)
        except RuntimeError as error:
            if "Issue #%s not found" % bug_no in error.args[0]:
                yield utils.fail("Issue %r not found" % bug_no)
                break
            else:
                raise

        if args.full:
            comments = args.api("comments", bug.number)
        else:
            comments = []
        if args.patch and bug.pull_request_url:
            request, body = args._http.request(bug.patch_url)
            patch = body.decode(charset_from_headers(request))
        else:
            patch = None
        yield tmpl.render(bug=bug, comments=comments, full=True, patch=patch)


@command
@argh.alias("open")
@label_add_arg
@stdin_arg
@title_arg
@body_arg
@argh.wrap_errors(template.EmptyMessageError)
def open_bug(args):
    "opening new bugs"
    if args.stdin:
        text = sys.stdin.readlines()
    elif not args.title:
        text = template.edit_text("open").splitlines()
    if args.stdin or not args.title:
        title = text[0]
        body = "\n".join(text[1:])
    else:
        title = args.title
        body = args.body
    bug = args.api("open", title, body)
    for string in args.add:
        args.api("add_label", bug.number, string)
    return utils.success("Bug %d opened" % bug.number)


@command
@stdin_arg
@message_arg
@bugs_arg
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
        except RuntimeError as error:
            if "Issue #%s not found" % bug in error.args[0]:
                yield utils.fail("Issue %r not found" % bug)
            else:
                raise


@command
@stdin_arg
@title_arg
@body_arg
@bugs_arg
@argh.wrap_errors(template.EmptyMessageError)
def edit(args):
    "editing bugs"
    if (args.title or args.stdin) and len(args.bugs) > 1:
        raise argh.CommandError("Can not use --stdin or command line "
                                "title/body with multiple bugs")
    for bug in args.bugs:
        if args.stdin:
            text = sys.stdin.readlines()
        elif not args.title:
            try:
                current = args.api("show", bug)
            except RuntimeError as error:
                if "Issue #%s not found" % bug in error.args[0]:
                    yield utils.fail("Issue %r not found" % bug)
                    continue
                else:
                    raise
            current_data = {"title": current.title, "body": current.body}
            text = template.edit_text("open", current_data).splitlines()
        if args.stdin or not args.title:
            title = text[0]
            body = "\n".join(text[1:])
        else:
            title = args.title
            body = args.body

        try:
            args.api("edit", bug, title, body)
        except RuntimeError as error:
            if "Issue #%s not found" % bug in error.args[0]:
                yield utils.fail("Issue %r not found" % bug)
            else:
                raise


@command
@stdin_arg
@message_arg
@bugs_arg
def close(args):
    "closing bugs"
    if args.stdin:
        message = sys.stdin.read()
    elif not args.message:
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
        except RuntimeError as error:
            if "Issue #%s not found" % bug in error.args[0]:
                yield utils.fail("Issue %r not found" % bug)
            else:
                raise


@command
@stdin_arg
@message_arg
@bugs_arg
def reopen(args):
    "reopening closed bugs"
    if args.stdin:
        message = sys.stdin.read()
    elif not args.message:
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
        except RuntimeError as error:
            if "Issue #%s not found" % bug in error.args[0]:
                yield utils.fail("Issue %r not found" % bug)
            else:
                raise


@command
@label_add_arg
@label_remove_arg
@bugs_arg
def label(args):
    "labelling bugs"
    for bug in args.bugs:
        try:
            for string in args.add:
                args.api("add_label", bug, string)
            for string in args.remove:
                args.api("remove_label", bug, string)
        except RuntimeError as error:
            if "Issue #%s not found" % bug in error.args[0]:
                yield utils.fail("Issue %r not found" % bug)
            else:
                raise


def main():
    """Main script"""
    description = __doc__.splitlines()[0].split("-", 1)[1]
    epilog = "Please report bugs to the JNRowe/hubugs project"
    parser = argh.ArghParser(description=description, epilog=epilog,
                             version="%%(prog)s %s" % __version__)
    parser.add_argument("-p", "--project", action=utils.ProjectAction,
                        help="GitHub project to operate on",
                        metavar="project")
    parser.add_argument("-u", "--host-url", default=None,
                        help="GitHub Enterprise host to connect to",
                        metavar="url")
    parser.add_commands(COMMANDS)
    try:
        parser.dispatch(pre_call=utils.set_api)
    except (EnvironmentError, utils.RepoError) as error:
        parser.error(error)
    except httplib2.ServerNotFoundError:
        raise parser.error("Project lookup failed.  Network or GitHub down?")
    except HttpError as error:
        if error.code == 404 and "Repository not found" in error.message:
            parser.error("Unknown project")
        else:
            parser.error(error.message)

if __name__ == '__main__':
    main()
