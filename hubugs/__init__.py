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

import atexit
import errno
import getpass
import logging
import os
# Used by raw_input, when imported
import readline  # NOQA
import sys

from base64 import b64encode

import click
import httplib2

logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S')
atexit.register(logging.shutdown)


from . import (template, utils)
from .i18n import _


class ProjectNameParamType(click.ParamType):

    """Project name parameter parser."""

    name = 'project'

    def convert(self, value, param, ctx):
        """Set fully qualified GitHub project name."""
        if '/' not in value:
            user = os.getenv('GITHUB_USER',
                             utils.get_git_config_val('github.user'))
            if not user:
                self.fail(_('No GitHub user setting!'))
            value = '%s/%s' % (user, value)
        return value


@click.group(help=_('Simple client for GitHub issues.'),
             epilog=_('Please report bugs at '
                      'https://github.com/JNRowe/hubugs/issues'),
             context_settings={'help_option_names': ['-h', '--help']})
@click.version_option(_version.dotted)
@click.option('--pager/--no-pager', help=_('Pass output through a pager.'))
@click.option('-p', '--project', type=ProjectNameParamType(),
              help=_('GitHub project to operate on.'))
@click.option('-u', '--host-url',
              default=utils.get_git_config_val('hubugs.host-url',
                                               'https://api.github.com'),
              help=_('GitHub Enterprise host to connect to.'))
@click.pass_context
def cli(ctx, pager, project, host_url):
    """Main command entry point.

    :param click.Context ctx: Current command context
    :param bool pager: Whether to page output
    :param str project: GitHub project name
    :param str host: Hostname to connect to
    """
    ctx.obj = utils.setup_environment(project, host_url)
    ctx.obj.update({
        'host_url': host_url,
        'pager': pager,
        'project': project,
    })


# Convenience wrappers for defining command arguments
def bugs_parser(f):
    f = click.argument('bugs', nargs=-1, type=click.INT)(f)
    return f


def message_parser(f):
    f = click.option('-m', '--message', help=_('Comment text.'))(f)
    return f


def attrib_parser(f):
    f = click.option('-o', '--order', default='number',
                     type=click.Choice(['number', 'updated']),
                     help=_('Sort order for listing bugs.'))(f)
    f = click.option('-s', '--state', default='open',
                     type=click.Choice(['open', 'closed', 'all']),
                     help=_('State of bugs to operate on.'))(f)
    return f


def stdin_parser(f):
    f = click.option('--stdin', is_flag=True,
                     help=_('Read message from standard input.'))(f)
    return f


def text_parser(f):
    f = click.option('--title')(f)
    f = click.option('--body')(f)
    return f


def label_parser(f):
    f = click.option('-a', '--add', multiple=True,
                     help=_('Add label to issue.'))(f)
    f = click.option('-c', '--create', multiple=True,
                     help=_('Create new label and add to issue.'))(f)
    return f


@cli.command(help=_('Setup GitHub access token.'))
@click.option('--local/--no-local',
              help=_('Set access token for local repository only.'))
@click.pass_obj
def setup(globs, local):
    """Setup GitHub access token."""
    if not utils.SYSTEM_CERTS:
        utils.warn(_('Falling back on bundled certificates'))
    if utils.CURL_CERTS:
        utils.warn(_('Using certs specified in $CURL_CERTS'))
    default_user = os.getenv('GITHUB_USER',
                             utils.get_git_config_val('github.user',
                                                      getpass.getuser()))
    user = click.prompt(_('GitHub user'), default_user)
    if not user:
        user = default_user
    password = click.prompt(_('GitHub password'), hide_input=True,
                            confirmation_prompt=True)

    private = click.confirm(_('Support private repositories'))

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
    utils.success(_('Configuration complete!'))


@cli.command(name='list', help=_('Listing bugs.'))
@click.option('-l', '--label', multiple=True,
              help=_('List bugs with specified label.'))
@click.option('-p', '--page', help=_('Page number.'), type=click.INT,
              default=1)
@click.option('-r', '--pull-requests', is_flag=True,
              help=_('List only pull requests.'))
@attrib_parser
@click.pass_obj
def list_bugs(globs, label, page, pull_requests, order, state):
    """Listing bugs."""
    bugs = []
    params = {}
    if pull_requests:
        # FIXME: Dirty solution to supporting PRs only, needs rethink
        url = '%s/repos/%s/pulls' % (globs.host_url, globs.project)
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


@cli.command(help=_('Searching bugs.'))
@attrib_parser
@click.argument('term')
@click.pass_obj
def search(globs, order, state, term):
    """Searching bugs."""
    search_url = '%s/search/issues' % globs.host_url
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


@cli.command(help=_('Displaying bugs.'))
@click.option('-f', '--full/--no-full', help=_('Show bug including comments.'))
@click.option('-p', '--patch/--no-patch', is_flag=True,
              help=_('Display patches for pull requests.'))
@click.option('-o', '--patch-only', is_flag=True,
              help=_('Display only the patch content of pull requests.'))
@click.option('-b', '--browse', is_flag=True,
              help=_('Open bug in web browser.'))
@bugs_parser
@click.pass_obj
def show(globs, full, patch, patch_only, browse, bugs):
    """Displaying bugs."""
    results = []
    tmpl = template.get_template('view', '/issue.txt')
    for bug_no in bugs:
        if browse:
            click.launch('https://github.com/%s/issues/%d'
                         % (globs.project, bug_no))
            continue
        r, bug = globs.req_get(bug_no, model='Issue')

        if full and bug.comments:
            r, comments = globs.req_get('%s/comments' % bug_no,
                                        model='Comment')
        else:
            comments = []
        if (patch or patch_only) and bug.pull_request:
            url = '%s/repos/%s/pulls/%s' % (globs.host_url, globs.project,
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


@cli.command(name='open', help=_('Opening new bugs.'))
@label_parser
@stdin_parser
@text_parser
@click.pass_obj
def open_bug(globs, add, create, stdin, title, body):
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
    utils.success(_('Bug %d opened') % bug.number)


@cli.command(help=_('Commenting on bugs.'))
@message_parser
@stdin_parser
@bugs_parser
@click.pass_obj
def comment(globs, message, stdin, bugs):
    """Commenting on bugs."""
    if stdin:
        message = click.get_text_stream().read()
    elif message:
        message = message
    else:
        message = template.edit_text()
    for bug in bugs:
        globs.req_post('%s/comments' % bug, body={'body': message},
                       model='Comment')


@cli.command(help=_('Editing bugs.'))
@stdin_parser
@text_parser
@bugs_parser
@click.pass_obj
def edit(globs, stdin, title, body, bugs):
    """Editing bugs."""
    if (title or stdin) and len(bugs) > 1:
        raise ValueError(_('Can not use --stdin or command line title/body '
                           'with multiple bugs'))
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


@cli.command(help=_('Closing bugs.'))
@stdin_parser
@message_parser
@bugs_parser
@click.pass_obj
def close(globs, stdin, message, bugs):
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
            globs.req_post('%s/comments' % bug, body={'body': message},
                           model='Comment')
        globs.req_post(bug, body={'state': 'closed'}, model='Issue')


@cli.command(help=_('Reopening closed bugs.'))
@stdin_parser
@message_parser
@bugs_parser
@click.pass_obj
def reopen(globs, stdin, message, bugs):
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
            globs.req_post('%s/comments' % bug, body={'body': message},
                           model='Comment')
        globs.req_post(bug, body={'state': 'open'}, model='Issue')


@cli.command(help=_('Labelling bugs.'))
@label_parser
@click.option('-r', '--remove', multiple=True,
              help=_('Remove label from issue.'))
@click.option('-l', '--list', is_flag=True, help=_('List available labels.'))
@click.argument('bugs', nargs=-1, required=False, type=click.INT)
@click.pass_obj
def label(globs, add, create, remove, list, bugs):
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


@cli.command(help=_('Issue milestones.'))
@click.argument('milestone')
@click.argument('bugs', nargs=-1, required=False, type=click.INT)
@click.pass_obj
def milestone(globs, milestone, bugs):
    """Issue milestones."""
    milestones_url = '%s/repos/%s/milestones' % (globs.host_url, globs.project)
    r, milestones = globs.req_get(milestones_url, model='Milestone')

    milestone_mapping = dict((m.title, m.number) for m in milestones)

    try:
        milestone = milestone_mapping[milestone]
    except KeyError:
        raise ValueError(_('No such milestone %r') % milestone)

    for bug_no in bugs:
        globs.req_post(bug_no, body={'milestone': milestone},
                       model='Milestone')


@cli.command(help=_('Repository milestones.'))
@click.option('-o', '--order', default='number',
              type=click.Choice(['number', 'due_date', 'completeness']),
              help=_('Sort order for listing bugs.'))
@click.option('-s', '--state', default='open',
              type=click.Choice(['open', 'closed']),
              help=_('State of milestones to operate on.'))
@click.option('-c', '--create', help=_('Create new milestone.'))
@click.option('-l', '--list', is_flag=True,
              help=_('List available milestones.'))
@click.pass_obj
def milestones(globs, order, state, create, list):
    """Repository milestones."""
    if not list and not create:
        utils.fail('No action specified!')
        return 1
    milestones_url = '%s/repos/%s/milestones' % (globs.host_url, globs.project)
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
        utils.success(_('Milestone %d created' % milestone.number))


@cli.command(help=_('Report a new bug against hubugs.'))
@click.pass_obj
def report_bug(globs):
    """Report a new bug against hubugs."""
    local = globs.project == 'JNRowe/hubugs'
    globs.project = 'JNRowe/hubugs'

    import html2text, jinja2, pygments  # NOQA
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
    utils.success(_('Bug %d opened against hubugs, thanks!') % bug.number)


def main():
    """Main command-line entry point.

    :rtype: ``int``
    :return: Exit code
    """
    try:
        cli()
    except utils.HttpClientError as error:
        utils.fail(error.content[0])
        return errno.EINVAL
    except httplib2.ServerNotFoundError:
        utils.fail(_('Project lookup failed.  Network or GitHub down?'))
        return errno.ENXIO
    except (utils.RepoError) as error:
        utils.fail(error.message)
        return errno.EINVAL
    except (EnvironmentError, ValueError) as error:
        utils.fail(error.message)
        return errno.EINVAL
