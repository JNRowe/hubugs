#
# coding=utf-8
"""hubugs - Simple client for GitHub issues"""
# Copyright © 2010-2016  James Rowe <jnrowe@gmail.com>
#           © 2012  Ben Griffiths
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
__author__ = 'James Rowe <jnrowe@gmail.com>'
__copyright__ = '2010-2016  James Rowe'
__license__ = 'GNU General Public License Version 3'
__credits__ = 'Ben Griffiths, Matt Leighton'
__history__ = 'See git repository'

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

import argparse
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

import aaargh
import httplib2

logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S')
atexit.register(logging.shutdown)


from . import (template, utils)
from .i18n import _


APP = aaargh.App(description=__doc__.splitlines()[0].split('-', 1)[1],
                 epilog=_('Please report bugs to the JNRowe/hubugs project'))

# Convenience wrappers for defining command arguments
# pylint: disable-msg=C0103
bugs_parser = argparse.ArgumentParser(add_help=False)
bugs_parser.add_argument('bugs', nargs='+', type=int,
                         help=_('bug number(s) to operate on'))

message_parser = argparse.ArgumentParser(add_help=False)
message_parser.add_argument('-m', '--message', help=_('comment text'))

attrib_parser = argparse.ArgumentParser(add_help=False)
attrib_parser.add_argument('-o', '--order', default='number',
                           choices=['number', 'updated'],
                           help=_('sort order for listing bugs'))
attrib_parser.add_argument('-s', '--state', default='open',
                           choices=['open', 'closed', 'all'],
                           help=_('state of bugs to operate on'))

stdin_parser = argparse.ArgumentParser(add_help=False)
stdin_parser.add_argument('--stdin', action='store_true',
                          help=_('read message from standard input'))

text_parser = argparse.ArgumentParser(add_help=False)
text_parser.add_argument('title', help=_('title for the new bug'), nargs='?')
text_parser.add_argument('body', help=_('body for the new bug'), nargs='?')

label_parser = argparse.ArgumentParser(add_help=False)
label_parser.add_argument('-a', '--add', action='append', default=[],
                          help=_('add label to issue'), metavar='label')
label_parser.add_argument('-c', '--create', action='append', default=[],
                          help=_('create new label and add to issue'),
                          metavar='label')
# pylint: enable-msg=C0103


@APP.cmd(help=_('setup GitHub access token'))
@APP.cmd_arg('--local', action='store_true',
             help=_('set access token for local repository only'))
def setup(args):
    """Setup GitHub access token."""
    if not utils.SYSTEM_CERTS:
        print(utils.warn(_('Falling back on bundled certificates')))
    if utils.CURL_CERTS:
        print(utils.warn(_('Using certs specified in $CURL_CERTS')))
    default_user = os.getenv('GITHUB_USER',
                             utils.get_git_config_val('github.user',
                                                      getpass.getuser()))
    try:
        user = raw_input(_('GitHub user? [%s] ') % default_user)
        if not user:
            user = default_user
        password = getpass.getpass(_('GitHub password? '))
    except KeyboardInterrupt:
        return

    result = raw_input(_('Support private repositories? [Y/n] '))
    private = result.lower() == _('y')

    data = {
        'scopes': ['repo' if private else 'public_repo'],
        'note': 'hubugs',
        'note_url': 'https://github.com/JNRowe/hubugs'
    }

    # Unfortunately, we need to forcibly define the header to workaround
    # GitHub sending a 404(in an effort to stop information leakage)
    header = {
        'Authorization': 'Basic ' + b64encode(':'.join([user, password]))
    }
    r, auth = args.req_post('https://api.github.com/authorizations', body=data,
                            headers=header, model='Authorisation')
    utils.set_git_config_val('hubugs.token', auth.token, args.local)
    print(utils.success(_('Configuration complete!')))


@APP.cmd(name='list', help=_('listing bugs'), parents=[attrib_parser, ])
@APP.cmd_arg('-l', '--label', help=_('list bugs with specified label'),
             metavar='label', action='append')
@APP.cmd_arg('-p', '--page', help=_('page number'), type=int, default=1,
             metavar='number')
@APP.cmd_arg('-r', '--pull-requests', action='store_true',
             help=_('list only pull requests'))
def list_bugs(args):
    """Listing bugs."""
    bugs = []
    params = {}
    if args.pull_requests:
        # FIXME: Dirty solution to supporting PRs only, needs rethink
        url = '%s/repos/%s/pulls' % (args.host_url, args.project)
    else:
        url = ''
    if args.page != 1:
        params['page'] = args.page
    if args.label:
        params['labels'] = ','.join(args.label)

    states = ['open', 'closed'] if args.state == 'all' else [args.state, ]
    for state in states:
        _params = params.copy()
        _params['state'] = state
        r, _bugs = args.req_get(url, params=_params, model='Issue')
        bugs.extend(_bugs)

    result = template.display_bugs(bugs, args.order, state=args.state,
                                   project=args.repo_obj)
    if result:
        utils.pager(result, pager=args.pager)


@APP.cmd(help=_('searching bugs'), parents=[attrib_parser, ])
@APP.cmd_arg('term', help=_('term to search bugs for'))
def search(args):
    """Searching bugs."""
    # This chunk of code is horrific, as is the models.from_search() that is
    # required to support it.  However, without search support in API v3 there
    # is no realistic way around it.
    from .models import from_search
    search_url = '%s/legacy/issues/search/%%s/%%s/%%s' % args.host_url
    states = ['open', 'closed'] if args.state == 'all' else [args.state, ]
    bugs = []
    for state in states:
        r, c = args.req_get(search_url % (args.project, state, args.term),
                            model='issue')
        _bugs = [from_search(d) for d in c.issues]
        bugs.extend(_bugs)
    result = template.display_bugs(bugs, args.order, term=args.term,
                                   state=args.state, project=args.repo_obj)
    if result:
        utils.pager(result, pager=args.pager)


@APP.cmd(help=_('displaying bugs'), parents=[bugs_parser, ])
@APP.cmd_arg('-f', '--full', action='store_true',
             help=_('show bug including comments'))
@APP.cmd_arg('-p', '--patch', action='store_true',
             help=_('display patches for pull requests'))
@APP.cmd_arg('-o', '--patch-only', action='store_true',
             help=_('display only the patch content of pull requests'))
@APP.cmd_arg('-b', '--browse', action='store_true',
             help=_('open bug in web browser'))
def show(args):
    """Displaying bugs."""
    results = []
    tmpl = template.get_template('view', '/issue.txt')
    for bug_no in args.bugs:
        if args.browse:
            webbrowser.open_new_tab('https://github.com/%s/issues/%d'
                                    % (args.project, bug_no))
            continue
        r, bug = args.req_get(bug_no, model='Issue')

        if args.full and bug.comments:
            r, comments = args.req_get('%s/comments' % bug_no, model='Comment')
        else:
            comments = []
        if (args.patch or args.patch_only) and bug.pull_request:
            url = '%s/repos/%s/pulls/%s' % (args.host_url, args.project,
                                            bug_no)
            headers = {'Accept': 'application/vnd.github.patch'}
            r, c = args.req_get(url, headers=headers, is_json=False)
            patch = c.decode('utf-8')
        else:
            patch = None
        results.append(tmpl.render(bug=bug, comments=comments, full=True,
                                   patch=patch, patch_only=args.patch_only,
                                   project=args.repo_obj))
    if results:
        utils.pager('\n'.join(results), pager=args.pager)


@APP.cmd(name='open', help=_('opening new bugs'),
         parents=[label_parser, stdin_parser, text_parser])
def open_bug(args):
    """Opening new bugs."""
    utils.sync_labels(args)
    if args.stdin:
        text = sys.stdin.readlines()
    elif not args.title:
        text = template.edit_text('open').splitlines()
    if args.stdin or not args.title:
        title = text[0]
        body = '\n'.join(text[1:])
    else:
        title = args.title
        body = args.body
    data = {'title': title, 'body': body, 'labels': args.add + args.create}
    r, bug = args.req_post('', body=data, model='Issue')
    print(utils.success(_('Bug %d opened') % bug.number))


@APP.cmd(help=_('commenting on bugs'),
         parents=[bugs_parser, stdin_parser, message_parser])
def comment(args):
    """Commenting on bugs."""
    if args.stdin:
        message = sys.stdin.read()
    elif args.message:
        message = args.message
    else:
        message = template.edit_text()
    for bug in args.bugs:
        args.req_post('%s/comments' % bug, body={'body': message},
                      model='Comment')


@APP.cmd(help=_('editing bugs'),
         parents=[bugs_parser, stdin_parser, text_parser])
def edit(args):
    """Editing bugs."""
    if (args.title or args.stdin) and len(args.bugs) > 1:
        raise ValueError(_('Can not use --stdin or command line title/body '
                           'with multiple bugs'))
    for bug in args.bugs:
        if args.stdin:
            text = sys.stdin.readlines()
        elif not args.title:
            r, current = args.req_get(bug, model='Issue')
            current_data = {'title': current.title, 'body': current.body}
            text = template.edit_text('open', current_data).splitlines()
        if args.stdin or not args.title:
            title = text[0]
            body = '\n'.join(text[1:])
        else:
            title = args.title
            body = args.body

        data = {'title': title, 'body': body}
        args.req_post(bug, body=data, model='Issue')


@APP.cmd(help=_('closing bugs'),
         parents=[bugs_parser, stdin_parser, message_parser])
def close(args):
    """Closing bugs."""
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
            args.req_post('%s/comments' % bug, body={'body': message},
                          model='Comment')
        args.req_post(bug, body={'state': 'closed'}, model='Issue')


@APP.cmd(help=_('reopening closed bugs'),
         parents=[bugs_parser, stdin_parser, message_parser])
def reopen(args):
    """Reopening closed bugs."""
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
            args.req_post('%s/comments' % bug, body={'body': message},
                          model='Comment')
        args.req_post(bug, body={'state': 'open'}, model='Issue')


@APP.cmd(help=_('labelling bugs'), parents=[label_parser, ])
@APP.cmd_arg('-r', '--remove', action='append', default=[],
             help=_('remove label from issue'), metavar='label')
@APP.cmd_arg('-l', '--list', action='store_true',
             help=_('list available labels'))
@APP.cmd_arg('bugs', nargs='*', type=int,
             help=_('bug number(s) to operate on'))
def label(args):
    """Labelling bugs."""
    label_names = utils.sync_labels(args)

    if args.list:
        print(', '.join(sorted(label_names)))
        return

    for bug_no in args.bugs:
        r, bug = args.req_get(bug_no, model='Issue')
        labels = [label.name for label in bug.labels]
        labels.extend(args.add + args.create)

        for string in args.remove:
            labels.remove(string)
        args.req_post(bug_no, body={'labels': labels}, model='Label')


@APP.cmd(help=_('issue milestones'))
@APP.cmd_arg('milestone', help=_('milestone to assign to'))
@APP.cmd_arg('bugs', nargs='*', type=int,
             help=_('bug number(s) to operate on'))
def milestone(args):
    """Issue milestones."""
    milestones_url = '%s/repos/%s/milestones' % (args.host_url, args.project)
    r, milestones = args.req_get(milestones_url, model='Milestone')

    milestone_mapping = dict((m.title, m.number) for m in milestones)

    try:
        milestone = milestone_mapping[args.milestone]
    except KeyError:
        raise ValueError(_('No such milestone %r') % args.milestone)

    for bug_no in args.bugs:
        args.req_post(bug_no, body={'milestone': milestone}, model='Milestone')


@APP.cmd(help=_('repository milestones'))
@APP.cmd_arg('-o', '--order', default='number',
             choices=['due_date', 'completeness'],
             help=_('sort order for listing bugs'))
@APP.cmd_arg('-s', '--state', default='open',
             choices=['open', 'closed'],
             help=_('state of milestones to operate on'))
@APP.cmd_arg('-c', '--create', help=_('create new milestone'),
             metavar='milestone')
@APP.cmd_arg('-l', '--list', action='store_true',
             help=_('list available milestones'))
def milestones(args):
    """Repository milestones."""
    if not args.list and not args.create:
        print(utils.fail('No action specified!'))
        return 1
    milestones_url = '%s/repos/%s/milestones' % (args.host_url, args.project)
    r, milestones = args.req_get(milestones_url, model='Milestone')

    if args.list:
        tmpl = template.get_template('view', '/list_milestones.txt')
        columns = utils.T.width if utils.T.width else 80
        max_id = max(i.number for i in milestones)
        id_len = len(str(max_id))

        result = tmpl.render(milestones=milestones, order=args.order,
                             state=args.state, project=args.repo_obj,
                             id_len=id_len, max_title=columns - id_len - 2)
        if result:
            utils.pager(result, pager=args.pager)
    elif args.create:
        data = {'title': args.create}
        r, milestone = args.req_post('', body=data, model='Milestone')
        print(utils.success(_('Milestone %d created' % milestone.number)))


@APP.cmd(name='report-bug', help=_('report a new bug against hubugs'))
def report_bug(args):
    """Report a new bug against hubugs."""
    local = args.project == 'JNRowe/hubugs'
    args.project = 'JNRowe/hubugs'

    import blessings, html2text, jinja2, pygments  # NOQA
    versions = dict([(m.__name__, getattr(m, '__version__', 'No version info'))
                     for m in (aaargh, blessings, html2text, httplib2, jinja2,
                               pygments)])
    data = {
        'local': local,
        'sys': sys,
        'version': _version.dotted,
        'versions': versions,
        'certs': utils.CA_CERTS,
    }
    text = template.edit_text('hubugs_report', data).splitlines()
    title = text[0]
    body = '\n'.join(text[1:])

    data = {'title': title, 'body': body, 'labels': args.add + args.create}
    r, bug = args.req_post('', body=data, model='Issue')
    print(utils.success(_('Bug %d opened against hubugs, thanks!')
                        % bug.number))


def main():
    """Main command-line entry point.

    :rtype: ``int``
    :return: Exit code
    """
    APP.arg('--version', action='version',
            version='%%(prog)s %s' % __version__)
    APP.arg('--pager', metavar='pager',
            default=utils.get_git_config_val('hubugs.pager',
                                             os.getenv('PAGER')),
            help=_('pass output through a pager'))
    APP.arg('--no-pager', action='store_false', dest='pager',
            help=_('do not pass output through pager'))
    APP.arg('-p', '--project', action=utils.ProjectAction,
            help=_('GitHub project to operate on'), metavar='project')
    APP.arg('-u', '--host-url',
            default=utils.get_git_config_val('hubugs.host-url',
                                             'https://api.github.com'),
            help=_('GitHub Enterprise host to connect to'), metavar='url')

    args = APP._parser.parse_args()

    try:
        utils.setup_environment(args)
        args._func(args)
    except utils.HttpClientError as error:
        print(utils.fail(error.content['message']))
        return errno.EINVAL
    except httplib2.ServerNotFoundError:
        print(utils.fail(_('Project lookup failed.  Network or GitHub down?')))
        return errno.ENXIO
    except (utils.RepoError) as error:
        print(utils.fail(error.message))
        return errno.EINVAL
    except (EnvironmentError, ValueError) as error:
        print(utils.fail(error.message))
        return errno.EINVAL
