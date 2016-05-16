#
# coding=utf-8
"""utils - Utility functions for hubugs"""
# Copyright © 2010-2016  James Rowe <jnrowe@gmail.com>
#           © 2012  Matt Leighton <mleighy@gmail.com>
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

import argparse
import json
import os
import re
import subprocess
import sys

from functools import partial

try:  # For Python 3
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode  # NOQA

import blessings
import configobj
import httplib2

from . import (_version, models)

from .i18n import _

PY3K = sys.version_info[0] == 3
if PY3K:
    unicode = str

T = blessings.Terminal()

try:
    # httplib2 0.8 and above support setting certs via ca_certs_locater module,
    # making this dirty mess even dirtier
    assert [int(i) for i in httplib2.__version__.split('.')] >= [0, 8]
    import ca_certs_locater
except (AssertionError, ImportError):
    _HTTPLIB2_BUNDLE = os.path.realpath(os.path.dirname(httplib2.CA_CERTS))
    SYSTEM_CERTS = \
        not _HTTPLIB2_BUNDLE.startswith(os.path.dirname(httplib2.__file__))
    CA_CERTS = None
    CURL_CERTS = False
    if not SYSTEM_CERTS and sys.platform.startswith('linux'):
        for cert_file in ['/etc/ssl/certs/ca-certificates.crt',
                          '/etc/pki/tls/certs/ca-bundle.crt']:
            if os.path.exists(cert_file):
                CA_CERTS = cert_file
                SYSTEM_CERTS = True
                break
    elif not SYSTEM_CERTS and sys.platform.startswith('freebsd'):
        if os.path.exists('/usr/local/share/certs/ca-root-nss.crt'):
            CA_CERTS = '/usr/local/share/certs/ca-root-nss.crt'
            SYSTEM_CERTS = True
    elif os.path.exists(os.getenv('CURL_CA_BUNDLE', '')):
        CA_CERTS = os.getenv('CURL_CA_BUNDLE')
        CURL_CERTS = True
    if not SYSTEM_CERTS and not CURL_CERTS:
        CA_CERTS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'GitHub_certs.crt')
else:
    CA_CERTS = ca_certs_locater.get()
    CURL_CERTS = False


# Set up informational message functions
def _colourise(text, colour):
    """Colour text, if possible.

    :param str text: Text to colourise
    :param str colour: Colour to display text in
    :rtype: ``str``
    :return: Colourised text, if possible
    """
    return getattr(T, colour.replace(' ', '_'))(text)


def success(text):
    """Output a success message.

    :param str text:  Text to format
    :rtype: ``str``
    :return: Bright green text, if possible
    """
    return _colourise(text, 'bright green')


def fail(text):
    """Output a failure message.

    :param str text:  Text to format
    :rtype: ``str``
    :return: Bright red text, if possible
    """
    return _colourise(text, 'bright red')


def warn(text):
    """Output a warning message.

    :param str text:  Text to format
    :rtype: ``str``
    :return: Bright yellow text, if possible
    """
    return _colourise(text, 'bright yellow')


class HttpClientError(ValueError):

    """Error raised for client error status codes."""

    def __init__(self, message, response, content):
        super(HttpClientError, self).__init__(message)
        self.response = response
        self.content = content


class RepoError(ValueError):

    """Error raised for invalid repository values."""


class ProjectAction(argparse.Action):

    """argparse action class for setting project."""

    def __call__(self, parser, namespace, project, option_string=None):
        """Set fully qualified GitHub project name."""
        if not '/' in project:
            user = os.getenv('GITHUB_USER', get_git_config_val('github.user'))
            if not user:
                raise parser.error(_('No GitHub user setting!'))
            project = '%s/%s' % (user, project)
        namespace.project = project


def check_output(args, **kwargs):
    """Simple check_output implementation for Python 2.6 compatibility.

    :param list args: Command and arguments to call
    :rtype: ``str``
    :return: Command output
    :raise subprocess.CalledProcessError: If command execution fails
    """
    try:
        output = subprocess.check_output(args, **kwargs)
    except AttributeError:
        process = subprocess.Popen(args, stdout=subprocess.PIPE, **kwargs)
        output, unused_err = process.communicate()
        retcode = process.poll()
        if retcode:
            raise subprocess.CalledProcessError(retcode, args[0])
    if PY3K:
        output = output.decode()
    return output


def get_github_api():
    """Create a GitHub API instance.

    :rtype: ``httplib2.Http``
    :return: GitHub HTTP session
    """
    if sys.platform == 'darwin':
        user_cache_dir = os.path.expanduser('~/Library/Caches')
    else:
        user_cache_dir = os.path.join(os.getenv('HOME', '/'), '.cache')
    xdg_cache_dir = os.getenv('XDG_CACHE_HOME')
    cache_dir = os.path.join(xdg_cache_dir or user_cache_dir, 'hubugs')

    return httplib2.Http(cache_dir, ca_certs=CA_CERTS)


def get_git_config_val(key, default=None, local_only=False):
    """Fetch a git configuration value.

    :param str key: Configuration value to fetch
    :param str default: Default value to use, if key isn't set
    :param bool local_only: Fetch configuration values from repo config only
    :rtype: ``str``
    :return: Git config value, if set
    """
    cmd = ['git', 'config', ]
    if local_only:
        cmd.append('--local')
    cmd.extend(['--get', key])
    try:
        output = check_output(cmd).strip()
    except subprocess.CalledProcessError:
        output = default
    return output


def set_git_config_val(key, value, local_only=False):
    """Set a git configuration value.

    :param str key: Configuration value to fetch
    :param str value: Value to set
    :param bool local_only: Set configuration values from repo config only
    """
    cmd = ['git', 'config', ]
    if not local_only:
        cmd.append('--global')
    cmd.extend([key, value])
    check_output(cmd, stderr=subprocess.STDOUT).strip()


def get_editor():
    """Choose a suitable editor.

    See :manpage:`git-var(1)` for details.

    :rtype: ``list`` of ``str``
    :return: Users chosen editor, or ``vi`` if not set
    """
    return check_output(['git', 'var', 'GIT_EDITOR']).strip().split()


def get_repo():
    """Extract GitHub project name from git/hg config.

    We check the git config for ``hubugs.project``, and then fall back to
    ``remote.origin.url``.  If both of these fail we check a mercurial root, to
    satisfy the ``hg-git`` users.

    :rtype: ``str``
    :return: GitHub project name, including user
    """
    data = get_git_config_val('hubugs.project', local_only=True)
    if data:
        return data
    data = get_git_config_val('remote.origin.url', local_only=True)
    if not data:
        try:
            root = check_output(['hg', 'root'], stderr=subprocess.PIPE).strip()
        except (OSError, subprocess.CalledProcessError):
            # No mercurial install, or not in a mercurial tree
            pass
        else:
            conf = configobj.ConfigObj(os.path.join(root, '.hg', 'hgrc'))
            try:
                data = conf['paths']['default']
            except KeyError:
                pass

    if not data:
        raise RepoError(_('Unable to guess project from repository'))

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
        raise RepoError(_('Invalid project configuration, specify with '
                          "`--project' option"))


def pager(text, pager='less'):
    """Pass output through pager.

    :param str text: Text to page
    :param bool pager: Pager to use
    """
    if pager:
        if 'less' in pager and 'LESS' not in os.environ:
            os.environ['LESS'] = 'FRSX'
        pager = subprocess.Popen([pager, ], stdin=subprocess.PIPE)
        if PY3K:
            pager.communicate(text.encode())
        else:
            pager.communicate(text)
    else:
        print(text)


def setup_environment(args):
    """Configure execution environment for commands dispatch.

    :param argparse.Namespace args: argparse namespace to operate on
    """
    if not args.project:
        args.project = get_repo()

    command = args._func.__name__

    http = get_github_api()

    HEADERS = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': _version.web,
    }

    # We use manual auth when calling setup
    if not command == 'setup':
        token = os.getenv('HUBUGS_TOKEN', get_git_config_val('hubugs.token'))
        if not token:
            raise EnvironmentError(_('No hubugs authorisation token found!  '
                                     "Run 'hubugs setup' to create a token"))
        HEADERS['Authorization'] = 'token %s' % token

    def http_method(url, method='GET', params=None, body=None, headers=None,
                    model=None, is_json=True):
        lheaders = HEADERS.copy()
        if headers:
            lheaders.update(headers)
        if not isinstance(url, (str, unicode)) or not url.startswith('http'):
            url = '%s/repos/%s/issues%s%s' % (args.host_url, args.project,
                                              '/' if url else '', url)
        if params:
            url += '?' + urlencode(params)
        if is_json and body:
            body = json.dumps(body)
        r, c = http.request(url, method=method, body=body, headers=lheaders)
        if is_json:
            c = json.loads(c.decode('utf-8'),
                           object_hook=partial(models.object_hook,
                                               name=model))
        if str(r.status)[0] == '4':
            raise HttpClientError(str(r.status), r, c)
        return r, c

    args.req_get = http_method
    args.req_post = partial(http_method, method='POST')

    # Make the repository information available, if it will be useful
    # Note: We skip this step for `show -b' for speed, see #20
    if not command == 'setup' and not (command == 'show'
                                       and args.browse is True):
        try:
            r, c = args.req_get('%s/repos/%s' % (args.host_url, args.project),
                                model='Repo')
        except HttpClientError as e:
            if e.content['message'] == 'Not Found':
                raise RepoError(_('Invalid project %r') % args.project)
            raise
        args.repo_obj = c
        if not args.repo_obj.has_issues:
            raise RepoError(("Issues aren't enabled for %r") % args.project)


def sync_labels(args):
    """Manage labels for a project.

    :param argparse.Namespace args: argparse namespace to operate on
    :rtype: ``list``
    :return: List of project's label names
    """
    labels_url = '%s/repos/%s/labels' % (args.host_url, args.project)
    r, c = args.req_get(labels_url, model='Label')
    label_names = [label.name for label in c]

    for label in args.add:
        if label not in label_names:
            raise ValueError(_('No such label %r') % label)
    for label in args.create:
        if label in label_names:
            print(warn(_('%r label already exists') % label))
        else:
            data = {'name': label, 'color': '000000'}
            args.req_post(labels_url, body=data, model='Label')
    return label_names + args.add + args.create
