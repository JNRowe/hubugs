#
"""hubugs - Simple client for GitHub issues.

``hubugs`` is a very simple client for working with `GitHub’s issue tracker`_.

.. _GitHub’s issue tracker: http://github.com/blog/411-github-issue-tracker
"""
# Copyright © 2010-2018  James Rowe <jnrowe@gmail.com>
#                        Ben Griffiths
#                        Matt Leighton <mleighy@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0+
#
# This file is part of hubugs.
#
# hubugs is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# hubugs is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# hubugs.  If not, see <http://www.gnu.org/licenses/>.

from . import _version


__version__ = _version.dotted
__date__ = _version.date
__copyright__ = '2010-2016  James Rowe'


# This is here to workaround UserWarning messages caused by path fiddling in
# dependencies
try:
    import pkg_resources  # NOQA: F401
except ImportError:
    pass

import atexit
import errno
import getpass
import logging
import os
# Used by raw_input, when imported
import readline  # NOQA: F401
import sys

from base64 import b64encode
from typing import Callable, List, Optional

import click
import httplib2

from jnrbase.attrdict import AttrDict
from jnrbase.colourise import fail, success, warn


logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(message)s',
                    datefmt='%FT%T')
atexit.register(logging.shutdown)


from . import (template, utils)


class ProjectNameParamType(click.ParamType):

    """Project name parameter parser."""

    name = 'project'

    def convert(self, __value: str, __param: Optional[click.Argument],
                __ctx: Optional[click.Context]) -> str:
        """Set fully qualified GitHub project name."""
        if '/' not in __value:
            user = os.getenv('GITHUB_USER',
                             utils.get_git_config_val('github.user'))
            if not user:
                raise click.BadParameter('No GitHub user setting!')
            __value = '/'.join([user, __value])
        return __value


@click.group(help='Simple client for GitHub issues.',
             epilog='Please report bugs at '
                    'https://github.com/JNRowe/hubugs/issues',
             context_settings={'help_option_names': ['-h', '--help']})
@click.version_option(_version.dotted)
@click.option('--pager/--no-pager', help='Pass output through a pager.')
@click.option('-p', '--project', type=ProjectNameParamType(),
              default=utils.get_repo(),
              help='GitHub project to operate on.')
@click.option('-u', '--host-url',
              default=utils.get_git_config_val('hubugs.host-url',
                                               'https://api.github.com'),
              help='GitHub Enterprise host to connect to.')
@click.pass_context
def cli(ctx: click.Context, pager: bool, project: str, host_url: str):
    """Main command entry point.

    Args:
        ctx: Current command context
        pager: Whether to page output
        project: GitHub project name
        host: Hostname to connect to
    """
    ctx.obj = utils.setup_environment(project, host_url)
    ctx.obj.update({
        'host_url': host_url,
        'pager': pager,
        'project': project,
    })


# Convenience wrappers for defining command arguments
def bugs_parser(__f: Callable) -> Callable:
    __f = click.argument('bugs', nargs=-1, type=click.INT)(__f)
    return __f


def message_parser(__f: Callable) -> Callable:
    __f = click.option('-m', '--message', help='Comment text.')(__f)
    return __f


def attrib_parser(__f: Callable) -> Callable:
    __f = click.option('-o', '--order', default='number',
                       type=click.Choice(['number', 'updated']),
                       help='Sort order for listing bugs.')(__f)
    __f = click.option('-s', '--state', default='open',
                       type=click.Choice(['open', 'closed', 'all']),
                       help='State of bugs to operate on.')(__f)
    return __f


def stdin_parser(__f: Callable) -> Callable:
    __f = click.option('--stdin', is_flag=True,
                       help='Read message from standard input.')(__f)
    return __f


def text_parser(__f: Callable) -> Callable:
    __f = click.option('--title')(__f)
    __f = click.option('--body')(__f)
    return __f


def label_parser(__f: Callable) -> Callable:
    __f = click.option('-a', '--add', multiple=True,
                       help='Add label to issue.')(__f)
    __f = click.option('-c', '--create', multiple=True,
                       help='Create new label and add to issue.')(__f)
    return __f


@cli.command()
@click.option('--local/--no-local',
              help='Set access token for local repository only.')
@click.pass_obj
def setup(globs: AttrDict, local: bool):
    """Setup GitHub access token."""
    if not utils.SYSTEM_CERTS:
        warn('Falling back on bundled certificates')
    if utils.CURL_CERTS:
        warn('Using certs specified in $CURL_CERTS')
    default_user = os.getenv('GITHUB_USER',
                             utils.get_git_config_val('github.user',
                                                      getpass.getuser()))
    user = click.prompt('GitHub user', default_user)
    if not user:
        user = default_user
    password = click.prompt('GitHub password', hide_input=True,
                            confirmation_prompt=False)

    private = click.confirm('Support private repositories')

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
    r, auth = globs.req_post('https://api.github.com/authorizations',
                             body=data, headers=header, model='Authorisation',
                             token=False)
    utils.set_git_config_val('hubugs.token', auth.token, local)
    success('Configuration complete!')


@cli.command(name='list')
@click.option('-l', '--label', multiple=True,
              help='List bugs with specified label.')
@click.option('-p', '--page', help='Page number.', type=click.INT,
              default=1)
@click.option('-r', '--pull-requests', is_flag=True,
              help='List only pull requests.')
@attrib_parser
@click.pass_obj
def list_bugs(globs: AttrDict, label: List[str], page: int,
              pull_requests: bool, order: str, state: str):
    """Listing bugs."""
    bugs = []
    params = {}
    if pull_requests:
        # FIXME: Dirty solution to supporting PRs only, needs rethink
        url = '{}/repos/{}/pulls'.format(globs.host_url, globs.project)
    else:
        url = ''
    if page != 1:
        params['page'] = page
    if label:
        params['labels'] = ','.join(label)

    states = ['open', 'closed'] if state == 'all' else [state, ]
    for state in states:
        _params = params.copy()
        _params['state'] = state
        r, _bugs = globs.req_get(url, params=_params, model='Issue')
        bugs.extend(_bugs)

    result = template.display_bugs(bugs, order, state=state,
                                   project=globs.repo_obj())
    if result:
        utils.pager(result, pager=globs.pager)


@cli.command()
@attrib_parser
@click.argument('term')
@click.pass_obj
def search(globs: AttrDict, order: str, state: str, term: str):
    """Searching bugs."""
    search_url = '{}/search/issues'.format(globs.host_url)
    states = ['open', 'closed'] if state == 'all' else [state, ]
    params = {
        'q': term,
        'repo': globs.project,
    }
    bugs = []
    for state in states:
        params['state'] = state
        r, c = globs.req_get(search_url, params=params, model='issue')
        bugs.extend(c.issues)
    result = template.display_bugs(bugs, order, term=term, state=state,
                                   project=globs.repo_obj())
    if result:
        utils.pager(result, pager=globs.pager)


@cli.command()
@click.option('-f', '--full/--no-full', help='Show bug including comments.')
@click.option('-p', '--patch/--no-patch', is_flag=True,
              help='Display patches for pull requests.')
@click.option('-o', '--patch-only', is_flag=True,
              help='Display only the patch content of pull requests.')
@click.option('-b', '--browse', is_flag=True,
              help='Open bug in web browser.')
@bugs_parser
@click.pass_obj
def show(globs: AttrDict, full: bool, patch: bool, patch_only: bool,
         browse: bool, bugs: List[int]):
    """Displaying bugs."""
    results = []
    tmpl = template.get_template('view', '/issue.txt')
    for bug_no in bugs:
        if browse:
            click.launch('https://github.com/{}/issues/{:d}'.format(
                globs.project, bug_no))
            continue
        r, bug = globs.req_get(bug_no, model='Issue')

        if full and bug.comments:
            r, comments = globs.req_get('{}/comments'.format(bug_no),
                                        model='Comment')
        else:
            comments = []
        if (patch or patch_only) and bug.pull_request:
            url = '{}/repos/{}/pulls/{}'.format(globs.host_url, globs.project,
                                                bug_no)
            headers = {'Accept': 'application/vnd.github.patch'}
            r, c = globs.req_get(url, headers=headers, is_json=False)
            patch = c.decode('utf-8')
        else:
            patch = None
        results.append(tmpl.render(bug=bug, comments=comments, full=True,
                                   patch=patch, patch_only=patch_only,
                                   project=globs.repo_obj()))
    if results:
        utils.pager('\n'.join(results), pager=globs.pager)


@cli.command(name='open')
@label_parser
@stdin_parser
@text_parser
@click.pass_obj
def open_bug(globs: AttrDict, add: List[str], create: List[str], stdin: bool,
             title: str, body: str):
    """Opening new bugs."""
    utils.sync_labels(globs, add, create)
    if stdin:
        text = click.get_text_stream('stdin').readlines()
    elif not title:
        text = template.edit_text('open').splitlines()
    if stdin or not title:
        title = text[0]
        body = '\n'.join(text[1:])
    else:
        title = title
        body = body
    data = {'title': title, 'body': body, 'labels': add + create}
    r, bug = globs.req_post('', body=data, model='Issue')
    success('Bug {:d} opened'.format(bug.number))


@cli.command()
@message_parser
@stdin_parser
@bugs_parser
@click.pass_obj
def comment(globs: AttrDict, message: str, stdin: bool, bugs: List[int]):
    """Commenting on bugs."""
    if stdin:
        message = click.get_text_stream().read()
    elif message:
        message = message
    else:
        message = template.edit_text()
    for bug in bugs:
        globs.req_post('{}/comments'.format(bug), body={'body': message},
                       model='Comment')


@cli.command()
@stdin_parser
@text_parser
@bugs_parser
@click.pass_obj
def edit(globs: AttrDict, stdin: bool, title: str, body:str, bugs: List[int]):
    """Editing bugs."""
    if (title or stdin) and len(bugs) > 1:
        raise ValueError('Can not use --stdin or command line title/body '
                         'with multiple bugs')
    for bug in bugs:
        if stdin:
            text = click.get_text_stream().readlines()
        elif not title:
            r, current = globs.req_get(bug, model='Issue')
            current_data = {'title': current.title, 'body': current.body}
            text = template.edit_text('open', current_data).splitlines()
        if stdin or not title:
            title = text[0]
            body = '\n'.join(text[1:])
        else:
            title = title
            body = body

        data = {'title': title, 'body': body}
        globs.req_post(bug, body=data, model='Issue')


@cli.command()
@stdin_parser
@message_parser
@bugs_parser
@click.pass_obj
def close(globs: AttrDict, stdin: bool, message: str, bugs: List[int]):
    """Closing bugs."""
    if stdin:
        message = click.get_text_stream().read()
    elif not message:
        try:
            message = template.edit_text()
        except template.EmptyMessageError:
            # Message isn't required for closing, but it is good practice
            message = None
    else:
        message = message
    for bug in bugs:
        if message:
            globs.req_post('{}/comments'.format(bug), body={'body': message},
                           model='Comment')
        globs.req_post(bug, body={'state': 'closed'}, model='Issue')


@cli.command()
@stdin_parser
@message_parser
@bugs_parser
@click.pass_obj
def reopen(globs: AttrDict, stdin: bool, message: str, bugs: List[int]):
    """Reopening closed bugs."""
    if stdin:
        message = click.get_text_stream().read()
    elif not message:
        try:
            message = template.edit_text()
        except template.EmptyMessageError:
            # Message isn't required for reopening, but it is good practice
            message = None
    for bug in bugs:
        if message:
            globs.req_post('{}/comments'.format(bug), body={'body': message},
                           model='Comment')
        globs.req_post(bug, body={'state': 'open'}, model='Issue')


@cli.command()
@label_parser
@click.option('-r', '--remove', multiple=True,
              help='Remove label from issue.')
@click.option('-l', '--list', is_flag=True, help='List available labels.')
@click.argument('bugs', nargs=-1, required=False, type=click.INT)
@click.pass_obj
def label(globs: AttrDict, add: List[str], create: List[str],
          remove: List[str], list: bool, bugs: List[int]):
    """Labelling bugs."""
    label_names = utils.sync_labels(globs, add, create)

    if list:
        click.echo(', '.join(sorted(label_names)))
        return

    for bug_no in bugs:
        r, bug = globs.req_get(bug_no, model='Issue')
        labels = [label.name for label in bug.labels]
        labels.extend(add + create)

        for string in remove:
            labels.remove(string)
        globs.req_post(bug_no, body={'labels': labels}, model='Label')


@cli.command()
@click.argument('milestone')
@click.argument('bugs', nargs=-1, required=False, type=click.INT)
@click.pass_obj
def milestone(globs: AttrDict, milestone: str, bugs: List[int]):
    """Issue milestones."""
    milestones_url = '{}/repos/{}/milestones'.format(globs.host_url,
                                                     globs.project)
    r, milestones = globs.req_get(milestones_url, model='Milestone')

    milestone_mapping = dict((m.title, m.number) for m in milestones)

    try:
        milestone = milestone_mapping[milestone]
    except KeyError:
        raise ValueError('No such milestone {:!r}'.format(milestone))

    for bug_no in bugs:
        globs.req_post(bug_no, body={'milestone': milestone},
                       model='Milestone')


@cli.command()
@click.option('-o', '--order', default='number',
              type=click.Choice(['number', 'due_date', 'completeness']),
              help='Sort order for listing bugs.')
@click.option('-s', '--state', default='open',
              type=click.Choice(['open', 'closed']),
              help='State of milestones to operate on.')
@click.option('-c', '--create', help='Create new milestone.')
@click.option('-l', '--list', is_flag=True,
              help='List available milestones.')
@click.pass_obj
def milestones(globs: AttrDict, order: str, state: str, create: str,
               list: bool):
    """Repository milestones."""
    if not list and not create:
        fail('No action specified!')
        return 1
    milestones_url = '{}/repos/{}/milestones'.format(globs.host_url,
                                                     globs.project)
    r, milestones = globs.req_get(milestones_url, model='Milestone')

    if list:
        tmpl = template.get_template('view', '/list_milestones.txt')
        columns = utils.T.width if utils.T.width else 80
        max_id = max(i.number for i in milestones)
        id_len = len(str(max_id))

        result = tmpl.render(milestones=milestones, order=order, state=state,
                             project=globs.repo_obj(),
                             id_len=id_len, max_title=columns - id_len - 2)
        if result:
            utils.pager(result, pager=globs.pager)
    elif create:
        data = {'title': create}
        r, milestone = globs.req_post('', body=data, model='Milestone')
        success('Milestone {:d} created'.format(milestone.number))


@cli.command()
@click.pass_obj
def report_bug(globs: AttrDict):
    """Report a new bug against hubugs."""
    local = globs.project == 'JNRowe/hubugs'
    globs.project = 'JNRowe/hubugs'

    import html2text, jinja2, pygments  # NOQA: E401
    versions = dict([(m.__name__, getattr(m, '__version__', 'No version info'))
                     for m in (click, html2text, httplib2, jinja2, pygments)])
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

    data = {'title': title, 'body': body}
    r, bug = globs.req_post('', body=data, model='Issue')
    success('Bug {:d} opened against hubugs, thanks!'.format(bug.number))


def main() -> int:
    """Main command-line entry point.

    Returns:
        Exit code
    """
    try:
        cli()
    except utils.HttpClientError as error:
        fail(error.content[0])
        return errno.EINVAL
    except httplib2.ServerNotFoundError:
        fail('Project lookup failed.  Network or GitHub down?')
        return errno.ENXIO
    except (utils.RepoError) as error:
        fail(error.args[0])
        return errno.EINVAL
    except (EnvironmentError, ValueError) as error:
        fail(error.args[1])
        return errno.EINVAL
