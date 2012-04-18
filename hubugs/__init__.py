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
import getpass
import json
import logging
import operator
import os
# Used by raw_input, when imported
import readline  # NOQA
import sys
import webbrowser

import argh
import requests


logging.basicConfig(level=logging.ERROR,
                    format="%(asctime)s - %(message)s",
                    datefmt="%Y-%m-%dT%H:%M:%S")
atexit.register(logging.shutdown)


from . import (models, template, utils)


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
@argh.arg('--local', default=False,
          help='set access token for local repository only')
def setup(args):
    "setup GitHub access token"
    default_user = os.getenv("GITHUB_USER",
                             utils.get_git_config_val("github.user",
                                                      getpass.getuser()))
    try:
        user = raw_input('GitHub user? [%s] ' % default_user)
        if not user:
            user = default_user
        password = getpass.getpass('GitHub password? ')
    except KeyboardInterrupt:
        return
    private = argh.confirm('Support private repositories', default=True)
    data = {
        'scopes': ['repo' if private else 'public_repo'],
        'note': 'hubugs',
        'note_url': 'https://github.com/JNRowe/hubugs'
    }

    auth = requests.auth.HTTPBasicAuth(user, password)
    r = requests.post('https://api.github.com/authorizations', auth=auth,
                      data=json.dumps(data))
    try:
        r.raise_for_status()
    except requests.HTTPError:
        raise argh.CommandError("Error generating token: %s"
                                % json.loads(r.content)['message'])
    auth = models.Authorisation.from_dict(r.content, is_json=True)
    utils.set_git_config_val('hubugs.token', auth.token, args.local)
    yield utils.success('Configuration complete!')


@command
@argh.alias("list")
@states_arg
@argh.arg("-l", "--label", help="list bugs with specified label",
          metavar="label")
@order_arg
def list_bugs(args):
    "listing bugs"
    bugs = []
    params = {}
    if args.label:
        params['labels'] = args.label

    states = ["open", "closed"] if args.state == "all" else [args.state, ]
    for state in states:
        _params = params.copy()
        _params['state'] = state
        r = args.req_get('', params=_params)
        bugs.extend(map(models.Issue.from_dict, json.loads(r.content)))

    return template.display_bugs(bugs, args.order, state=args.state)


@command
@argh.arg("-f", "--full", default=False, help="show bug including comments")
@argh.arg("-p", "--patch", default=False,
          help="display patches for pull requests")
@argh.arg("-o", "--patch-only", default=False,
          help="display only the patch content of pull requests")
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
            r = args.req_get(bug_no)
            bug = models.Issue.from_dict(r.content, is_json=True)
        except RuntimeError as error:
            if "Issue #%s not found" % bug_no in error.args[0]:
                yield utils.fail("Issue %r not found" % bug_no)
                break
            else:
                raise

        if args.full and bug.comments:
            r = args.req_get('%s/comments' % bug_no)
            comments = map(models.Comment.from_dict, json.loads(r.content))
        else:
            comments = []
        if (args.patch or args.patch_only) and bug.pull_request:
            patch = args.session.get(bug.pull_request.patch_url).content
        else:
            patch = None
        yield tmpl.render(bug=bug, comments=comments, full=True,
                          patch=patch, patch_only=args.patch_only)


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
    data = {'title': title, 'body': body, 'labels': args.add}
    r = args.req_post('', data=json.dumps(data))
    bug = models.Issue.from_dict(r.content, is_json=True)
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
            args.req_post('%s/comments' % bug,
                          data=json.dumps({'body': message}))
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
                r = args.req_get(bug)
                current = models.Issue.from_dict(r.content, is_json=True)
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
            data = {'title': title, 'body': body}
            args.req_post(bug, data=json.dumps(data))
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
                args.req_post('%s/comments' % bug,
                              data=json.dumps({'body': message}))
            args.req_post(bug, data=json.dumps({'state': 'closed'}))
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
                args.req_post('%s/comments' % bug,
                              data=json.dumps({'body': message}))
            args.req_post(bug, data=json.dumps({'state': 'open'}))
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
    for bug_no in args.bugs:
        r = args.req_get(bug_no)
        bug = models.Issue.from_dict(r.content, is_json=True)
        labels = map(operator.attrgetter('name'), bug.labels)
        labels.extend(args.add)
        for string in args.remove:
            labels.remove(string)
        try:
            r = args.req_post(bug_no, data=json.dumps({'labels': labels}))
        except RuntimeError as error:
            if "Issue #%s not found" % bug_no in error.args[0]:
                yield utils.fail("Issue %r not found" % bug_no)
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
    parser.add_argument("-u", "--host-url", default='https://api.github.com',
                        help="GitHub Enterprise host to connect to",
                        metavar="url")
    parser.add_commands(COMMANDS)
    try:
        parser.dispatch(pre_call=utils.set_api)
    except (EnvironmentError, utils.RepoError) as error:
        parser.error(error)
    except requests.ConnectionError:
        raise parser.error("Project lookup failed.  Network or GitHub down?")
    except requests.HTTPError as error:
        if error.code == 404 and "Repository not found" in error.message:
            parser.error("Unknown project")
        else:
            parser.error(error.message)

if __name__ == '__main__':
    main()
