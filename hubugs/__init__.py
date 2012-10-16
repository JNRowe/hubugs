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

# This is here to workaround UserWarning messages caused by path fiddling in
# dependencies
try:
    import pkg_resources  # NOQA
except ImportError:
    pass

import atexit
import errno
import getpass
import logging
import os
# Used by raw_input, when imported
import readline  # NOQA
import sys
import webbrowser

from base64 import b64encode

import argh
import httplib2

from kitchen.text.converters import to_unicode
from schematics.base import TypeException


logging.basicConfig(level=logging.ERROR,
                    format="%(asctime)s - %(message)s",
                    datefmt="%Y-%m-%dT%H:%M:%S")
atexit.register(logging.shutdown)


from . import (template, utils)
from .i18n import _


COMMANDS = []


def command(func):
    """Simple decorator to add function to ``COMMANDS`` list.

    The purpose of this decorator is to make the definition of commands simpler
    by reducing duplication, it is purely a convenience.

    :param func func: Function to wrap
    :rtype: ``func``
    :returns: Original function

    """
    COMMANDS.append(func)
    return func


# Convenience wrappers for defining command arguments
# pylint: disable-msg=C0103
bugs_arg = argh.arg("bugs", nargs="+", type=int,
                    help=_("bug number(s) to operate on"))

message_arg = argh.arg("-m", "--message", help=_("comment text"))

order_arg = argh.arg("-o", "--order", default="number",
                     choices=["number", "updated"],
                     help=_("sort order for listing bugs"))

states_arg = argh.arg("-s", "--state", default="open",
                      choices=["open", "closed", "all"],
                      help=_("state of bugs to operate on"))

stdin_arg = argh.arg("--stdin", default=False,
                     help=_("read message from standard input"))

title_arg = argh.arg("title", help=_("title for the new bug"), nargs="?")
body_arg = argh.arg("body", help=_("body for the new bug"), nargs="?")

label_add_arg = argh.arg("-a", "--add", action="append", default=[],
                         help=_("add label to issue"), metavar="label")
label_create_arg = argh.arg("-c", "--create", action="append", default=[],
                            help=_("create new label and add to issue"),
                            metavar="label")
label_remove_arg = argh.arg("-r", "--remove", action="append", default=[],
                            help=_("remove label from issue"), metavar="label")
# pylint: enable-msg=C0103


@command
@argh.arg('--local', default=False,
          help='set access token for local repository only')
def setup(args):
    if not utils.SYSTEM_CERTS:
        yield utils.warn(_('Falling back on bundled certificates'))
    if utils.CURL_CERTS:
        yield utils.warn(_('Using certs specified in $CURL_CERTS'))
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

    # Unfortunately, we need to forcibly define the header to workaround
    # GitHub sending a 404(in an effort to stop information leakage)
    header = {
        'Authorization': 'Basic ' + b64encode(":".join([user, password]))
    }
    r, auth = args.req_post('https://api.github.com/authorizations', body=data,
                            headers=header, model='Authorisation')
    utils.set_git_config_val('hubugs.token', auth.token, args.local)
    yield utils.success(_('Configuration complete!'))
setup.__doc__ = _("setup GitHub access token")


@command
@argh.alias("list")
@states_arg
@argh.arg("-l", "--label", help=_("list bugs with specified label"),
          metavar="label", action="append")
@order_arg
def list_bugs(args):
    bugs = []
    params = {}
    if args.label:
        params['labels'] = ",".join(args.label)

    states = ["open", "closed"] if args.state == "all" else [args.state, ]
    for state in states:
        _params = params.copy()
        _params['state'] = state
        r, _bugs = args.req_get('', params=_params, model=['Issue', ])
        bugs.extend(_bugs)

    yield template.display_bugs(bugs, args.order, state=args.state,
                                project=args.repo_obj)
list_bugs.__doc__ = _("listing bugs")


@command
@states_arg
@order_arg
@argh.arg("term", help=_("term to search bugs for"))
def search(args):
    # This chunk of code is horrific, as is the Issue.from_search() that is
    # required to support it.  However, without search support in API v3 there
    # is realistic way around it.
    from .models import Issue
    search_url = 'https://api.github.com/legacy/issues/search/%s/%s/%s'
    states = ["open", "closed"] if args.state == "all" else [args.state, ]
    bugs = []
    for state in states:
        r, c = args.req_get(search_url % (args.project, state, args.term))
        _bugs = [Issue.from_search(d) for d in c['issues']]
        bugs.extend(_bugs)
    return template.display_bugs(bugs, args.order, term=args.term,
                                 state=args.state, project=args.repo_obj)

search.__doc__ = _("searching bugs")


@command
@argh.arg("-f", "--full", default=False, help=_("show bug including comments"))
@argh.arg("-p", "--patch", default=False,
          help=_("display patches for pull requests"))
@argh.arg("-o", "--patch-only", default=False,
          help=_("display only the patch content of pull requests"))
@argh.arg("-b", "--browse", default=False, help=_("open bug in web browser"))
@bugs_arg
def show(args):
    tmpl = template.get_template('view', '/issue.txt')
    for bug_no in args.bugs:
        if args.browse:
            webbrowser.open_new_tab("https://github.com/%s/issues/%d"
                                    % (args.project, bug_no))
            continue
        r, bug = args.req_get(bug_no, model='Issue')

        if args.full and bug.comments:
            r, comments = args.req_get('%s/comments' % bug_no,
                                       model=['Comment', ])
        else:
            comments = []
        if (args.patch or args.patch_only) and bug.pull_request:
            r, c = args.req_get(bug.pull_request.patch_url, is_json=False)
            patch = to_unicode(c)
        else:
            patch = None
        yield tmpl.render(bug=bug, comments=comments, full=True,
                          patch=patch, patch_only=args.patch_only,
                          project=args.repo_obj)
show.__doc__ = _("displaying bugs")


@command
@argh.alias("open")
@label_add_arg
@label_create_arg
@stdin_arg
@title_arg
@body_arg
@argh.wrap_errors(template.EmptyMessageError)
def open_bug(args):
    utils.sync_labels(args)
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
    data = {'title': title, 'body': body, 'labels': args.add + args.create}
    r, bug = args.req_post('', body=data, model='Issue')
    yield utils.success(_("Bug %d opened") % bug.number)
open_bug.__doc__ = _("opening new bugs")


@command
@stdin_arg
@message_arg
@bugs_arg
@argh.wrap_errors(template.EmptyMessageError)
def comment(args):
    if args.stdin:
        message = sys.stdin.read()
    elif args.message:
        message = args.message
    else:
        message = template.edit_text()
    for bug in args.bugs:
        args.req_post('%s/comments' % bug, body={'body': message})
comment.__doc__ = _("commenting on bugs")


@command
@stdin_arg
@title_arg
@body_arg
@bugs_arg
@argh.wrap_errors(template.EmptyMessageError)
def edit(args):
    if (args.title or args.stdin) and len(args.bugs) > 1:
        raise argh.CommandError(_("Can not use --stdin or command line "
                                  "title/body with multiple bugs"))
    for bug in args.bugs:
        if args.stdin:
            text = sys.stdin.readlines()
        elif not args.title:
            r, current = args.req_get(bug, model='Issue')
            current_data = {"title": current.title, "body": current.body}
            text = template.edit_text("open", current_data).splitlines()
        if args.stdin or not args.title:
            title = text[0]
            body = "\n".join(text[1:])
        else:
            title = args.title
            body = args.body

        data = {'title': title, 'body': body}
        args.req_post(bug, body=data)
edit.__doc__ = _("editing bugs")


@command
@stdin_arg
@message_arg
@bugs_arg
def close(args):
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
        if message:
            args.req_post('%s/comments' % bug, body={'body': message})
        args.req_post(bug, body={'state': 'closed'})
close.__doc__ = _("closing bugs")


@command
@stdin_arg
@message_arg
@bugs_arg
def reopen(args):
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
        if message:
            args.req_post('%s/comments' % bug, body={'body': message})
        args.req_post(bug, body={'state': 'open'})
reopen.__doc__ = _("reopening closed bugs")


@command
@label_add_arg
@label_create_arg
@label_remove_arg
@argh.arg("-l", "--list", default=False, help="list available labels")
@argh.arg("bugs", nargs="*", type=int,
          help="bug number(s) to operate on")
def label(args):
    label_names = utils.sync_labels(args)

    if args.list:
        print ", ".join(sorted(label_names))
        return

    for bug_no in args.bugs:
        r, bug = args.req_get(bug_no, model='Issue')
        labels = [label.name for label in bug.labels]
        labels.extend(args.add + args.create)

        for string in args.remove:
            labels.remove(string)
        args.req_post(bug_no, body={'labels': labels})
label.__doc__ = _("labelling bugs")


@command
@argh.wrap_errors(template.EmptyMessageError)
def report_bug(args):
    local = args.project == 'JNRowe/hubugs'
    args.project = 'JNRowe/hubugs'

    import blessings, html2text, jinja2, pygments, schematics # NOQA
    versions = dict([(m.__name__, getattr(m, '__version__', 'No version info'))
                     for m in argh, blessings, html2text, httplib2, jinja2,
                        pygments, schematics])
    data = {
        'local': local,
        'sys': sys,
        'version': _version.dotted,
        'versions': versions,
        'certs': utils.CA_CERTS,
    }
    text = template.edit_text("hubugs_report", data).splitlines()
    title = text[0]
    body = "\n".join(text[1:])

    data = {'title': title, 'body': body, 'labels': args.add + args.create}
    r, bug = args.req_post('', body=data, model='Issue')
    yield utils.success(_("Bug %d opened against hubugs, thanks!")
                        % bug.number)
report_bug.__doc__ = _("report a new bug against hubugs")


def main():
    """Main command-line entry point.

    :rtype: ``int``
    :return: Exit code

    """
    description = __doc__.splitlines()[0].split("-", 1)[1]
    epilog = _("Please report bugs to the JNRowe/hubugs project")
    parser = argh.ArghParser(description=description, epilog=epilog,
                             version="%%(prog)s %s" % __version__)
    parser.add_argument("-p", "--project", action=utils.ProjectAction,
                        help=_("GitHub project to operate on"),
                        metavar="project")
    parser.add_argument("-u", "--host-url", default='https://api.github.com',
                        help="GitHub Enterprise host to connect to",
                        metavar="url")
    parser.add_commands(COMMANDS)
    try:
        parser.dispatch(pre_call=utils.setup_environment)
    except (utils.RepoError, EnvironmentError, ValueError) as error:
        print utils.fail(error.message)
        return errno.EINVAL
    except httplib2.ServerNotFoundError:
        print utils.fail(_("Project lookup failed.  Network or GitHub down?"))
        return errno.ENXIO
    except TypeException:
        print utils.fail(_("API modelling failed.  Please report this!"))

if __name__ == '__main__':
    sys.exit(main())
