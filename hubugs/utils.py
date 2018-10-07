#
"""utils - Utility functions for hubugs."""
# Copyright © 2011-2018  James Rowe <jnrowe@gmail.com>
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

import configparser
import json
import os
import re
import subprocess
import sys

from functools import partial
from typing import List, Optional
from urllib.parse import urlencode

import click
import httplib2

from jnrbase.attrdict import AttrDict
from jnrbase.colourise import warn
from jnrbase.xdg_basedir import user_cache

from . import (_version, models)

try:
    import ca_certs_locater
    CA_CERTS = ca_certs_locater.get()
except ImportError:
    CA_CERTS = None


class HttpClientError(ValueError):

    """Error raised for client error status codes."""

    def __init__(self, message, response, content):
        super(HttpClientError, self).__init__(message)
        self.response = response
        self.content = content


class RepoError(ValueError):

    """Error raised for invalid repository values."""


def get_github_api():
    """Create a GitHub API instance.

    Returns:
        httplib2.Http: GitHub HTTP session
    """
    cache_dir = user_cache('hubugs')
    with open('{}/CACHEDIR.TAG'.format(cache_dir), 'w') as f:
        f.writelines([
            'Signature: 8a477f597d28d172789f06886806bc55\n',
            '# This file is a cache directory tag created by hubugs.\n',
            '# For information about cache directory tags, see:\n',
            '#   http://www.brynosaurus.com/cachedir/\n',
            ])
    return httplib2.Http(cache_dir, ca_certs=CA_CERTS)


def get_git_config_val(__key: str, default: Optional[str] = None,
                       local_only: Optional[bool] = False) -> str:
    """Fetch a git configuration value.

    Args:
        __key: Configuration value to fetch
        default: Default value to use, if key isn’t set
        local_only: Fetch configuration values from repo config only

    Return:
        Git config value, if set
    """
    cmd = ['git', 'config', ]
    if local_only:
        cmd.append('--local')
    cmd.extend(['--get', __key])
    try:
        output = subprocess.check_output(cmd).decode().strip()
    except subprocess.CalledProcessError:
        output = default
    if output and output.startswith('!'):
        try:
            output = subprocess.check_output(output[1:].split())
            output = output.decode().strip()
        except subprocess.CalledProcessError:
            print('Whoops!')
            sys.exit(97)
    return output


def set_git_config_val(__key: str, __value: str,
                       local_only: Optional[bool] = False):
    """Set a git configuration value.

    Args:
        __key: Configuration value to fetch
        __value: Value to set
        local_only: Set configuration values from repo config only
    """
    cmd = ['git', 'config', ]
    if not local_only:
        cmd.append('--global')
    cmd.extend([__key, value])
    subprocess.check_output(cmd, stderr=subprocess.STDOUT)


def get_editor() -> List[str]:
    """Choose a suitable editor.

    See :manpage:`git-var(1)` for details.

    Return:
        Users chosen editor, or ``vi`` if not set
    """
    output = subprocess.check_output(['git', 'var', 'GIT_EDITOR'])
    return output.decode().strip().split()


def get_repo() -> str:
    """Extract GitHub project name from git/hg config.

    We check the git config for ``hubugs.project``, and then fall back to
    ``remote.origin.url``.  If both of these fail we check a mercurial root, to
    satisfy the ``hg-git`` users.

    Returns:
        GitHub project name, including user
    """
    data = get_git_config_val('hubugs.project', local_only=True)
    if data:
        return data
    data = get_git_config_val('remote.origin.url', local_only=True)
    if not data:
        try:
            root = subprocess.check_output(['hg', 'root'],
                                           stderr=subprocess.PIPE)
            root = root.decode().strip()
        except (OSError, subprocess.CalledProcessError):
            # No mercurial install, or not in a mercurial tree
            pass
        else:
            conf = configparser.ConfigParser()
            conf.read(os.path.join(root, '.hg', 'hgrc'))
            with contextlib.suppress(configparser.NoSectionError,
                                     configparser.NoOptionError):
                data = conf.get('paths', 'default')

    if not data:
        raise RepoError('Unable to guess project from repository')

    match = re.match(
        r"""
        (?:git(?:@|://)  # SSH or git protocol
          |git\+ssh://(?:git@)  # hg-git SSH URLs
          |https?://
           (?:.*@)?)  # HTTP URLs support optional auth data
        github.com[:/]  # hostname, : sep for SSH URL
        ([^/]+/.*?)  # project
        (?:.git)?$  # .git suffix is optional in all clone URLs
        """,
        data, re.VERBOSE)
    if match:
        return match.groups()[0]
    else:
        raise RepoError('Invalid project configuration, specify with '
                        "‘--project’ option")


def pager(__text: str, pager: Optional[bool] = False):
    """Pass output through pager.

    Args:
        __text: Text to page
        pager: Pager to use
    """
    if pager:
        click.echo_via_pager(__text)
    else:
        click.echo(__text)


def setup_environment(__project, __host_url):
    """Configure execution environment for commands dispatch."""
    env = AttrDict()

    if not __project:
        __project = get_repo()

    http = get_github_api()

    base_headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': _version.web,
    }

    token = os.getenv('HUBUGS_TOKEN', get_git_config_val('hubugs.token', None))
    if token:
        base_headers['Authorization'] = 'token {}'.format(token)

    def http_method(__url, method='GET', params=None, body=None, headers=None,
                    model=None, is_json=True, token=True):
        lheaders = base_headers.copy()
        if token and 'Authorization' not in lheaders:
            raise EnvironmentError('No hubugs authorisation token found!  '
                                   "Run ‘hubugs setup’ to create a token")
        if headers:
            lheaders.update(headers)
        if not isinstance(__url, str) or not __url.startswith('http'):
            __url = '{}/repos/{}/issues{}{}'.format(__host_url, __project,
                                                    '/' if __url else '',
                                                    __url)
        if params:
            __url += '?' + urlencode(params)
        if is_json and body:
            body = json.dumps(body)
        r, c = http.request(__url, method=method, body=body, headers=lheaders)
        if is_json:
            c = json.loads(c.decode('utf-8'),
                           object_hook=partial(models.object_hook,
                                               __name=model))
        if str(r.status)[0] == '4':
            raise HttpClientError(str(r.status), r, c)
        return r, c

    env['req_get'] = http_method
    env['req_post'] = partial(http_method, method='POST')

    def repo_obj():
        r, c = http_method('{}/repos/{}'.format(__host_url, __project),
                           model='Repo')
        if not c.has_issues:
            raise RepoError(
                "Issues aren’t enabled for {:!r}".format(__project))
    env['repo_obj'] = repo_obj
    return env


def sync_labels(__globs: AttrDict, __add, __create) -> List[str]:
    """Manage labels for a project.

    Args:
        globs: Global argument configuration

    Returns:
        List of project’s label names
    """
    labels_url = '{}/repos/{}/labels'.format(__globs.host_url, __globs.project)
    r, c = globs.req_get(labels_url, model='Label')
    label_names = [label.name for label in c]

    for label in __add:
        if label not in label_names:
            raise ValueError('No such label {!r}'.format(label))
    for label in __create:
        if label in label_names:
            warn('{!r} label already exists'.format(label))
        else:
            data = {'name': label, 'color': '000000'}
            globs.req_post(labels_url, body=data, model='Label')
    return label_names + add + create
