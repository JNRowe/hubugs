#
# coding=utf-8
"""utils - Utility functions for hubugs"""
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

import json
import os
import re
import subprocess
import sys
import urllib

from functools import partial

import argh
import blessings
import httplib2

from . import (_version, models)

from .i18n import _


T = blessings.Terminal()

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
                            "GitHub_certs.crt")


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
    :rtype: ``str`
    :return: Bright green text, if possible

    """
    return _colourise(text, 'bright green')


def fail(text):
    """Output a failure message.

    :param str text:  Text to format
    :rtype: ``str`
    :return: Bright red text, if possible

    """
    return _colourise(text, 'bright red')


def warn(text):
    """Output a warning message.

    :param str text:  Text to format
    :rtype: ``str`
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


class ProjectAction(argh.utils.argparse.Action):

    """argparse action class for setting project."""

    def __call__(self, parser, namespace, project, option_string=None):
        """Set fully qualified GitHub project name."""
        if not "/" in project:
            user = os.getenv("GITHUB_USER", get_git_config_val("github.user"))
            if not user:
                raise parser.error(_("No GitHub user setting!"))
            project = "%s/%s" % (user, project)
        namespace.project = project


def check_output(args, **kwargs):
    """Simple check_output implementation for Python 2.6 compatibility.

    :param list args: Command and arguments to call
    :rtype: ``str``
    :return: Command output
    :raise subprocess.CalledProcessError: If command execution fails

    """
    try:
        return subprocess.check_output(args, **kwargs)
    except AttributeError:
        process = subprocess.Popen(args, stdout=subprocess.PIPE, **kwargs)
        output, unused_err = process.communicate()
        retcode = process.poll()
        if retcode:
            raise subprocess.CalledProcessError(retcode, args[0])
        return output


def get_github_api():
    """Create a GitHub API instance.

    :rtype: ``httplib2.Http``
    :return: GitHub HTTP session

    """
    if sys.platform == 'darwin':
        user_cache_dir = os.path.expanduser("~/Library/Caches")
    else:
        user_cache_dir = os.path.join(os.getenv("HOME", "/"), ".cache")
    xdg_cache_dir = os.getenv("XDG_CACHE_HOME")
    cache_dir = os.path.join(xdg_cache_dir or user_cache_dir, "hubugs")

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
    try:
        check_output(cmd, stderr=subprocess.STDOUT).strip()
    except subprocess.CalledProcessError as e:
        raise argh.CommandError(e.output)


def get_editor():
    """Choose a suitable editor.

    See :manpage:`git-var(1)` for details.

    :rtype: ``list`` of ``str``
    :return: Users chosen editor, or ``vi`` if not set

    """
    return check_output(['git', 'var', 'GIT_EDITOR']).strip().split()


def get_repo():
    """Extract GitHub project name from git config.

    :rtype: ``str``
    :return: GitHub project name, including user

    """
    data = get_git_config_val("remote.origin.url", local_only=True)
    if not data:
        raise RepoError(_("No `origin' remote found"))
    match = re.match(r"""
        (?:git(?:@|://)  # SSH or git protocol
          |https?://
           (?:.*@)?)  # HTTP URLs support optional auth data
        github.com[:/]  # hostname, : sep for SSH URL
        ([^/]+/.*?)  # project
        (?:.git)?$  # .git suffix is optional in all clone URLs""",
                     data, re.VERBOSE)
    if match:
        return match.groups()[0]
    else:
        raise RepoError(_("Unknown project, specify with `--project' option"))


def setup_environment(args):
    """Configure execution environment for commands dispatch.

    :param argparse.Namespace args: argparse namespace to operate on

    """
    if not args.project:
        args.project = get_repo()

    command = args.function.__name__

    http = get_github_api()

    HEADERS = {
        'Accept': 'application/vnd.github.beta.full+json',
        'User-Agent': _version.web,
    }

    # We use manual auth when calling setup
    use_auth = not command == 'setup'
    if use_auth:
        token = os.getenv("HUBUGS_TOKEN", get_git_config_val("hubugs.token"))
        if not token:
            raise EnvironmentError(_("No hubugs authorisation token found!  "
                                   "Run 'hubugs setup' to create a token"))
        HEADERS["Authorization"] = "token %s" % token

    def http_method(url, method='GET', params=None, body=None, headers=None,
                    model=None, is_json=True):
        if headers:
            headers.update(HEADERS)
        else:
            headers = HEADERS
        if not isinstance(url, basestring) or not url.startswith('http'):
            url = '%s/repos/%s/issues%s%s' % (args.host_url, args.project,
                                              '/' if url else '', url)
        if params:
            url += '?' + urllib.urlencode(params)
        if is_json and body:
            body = json.dumps(body)
        r, c = http.request(url, method=method, body=body, headers=headers)
        if is_json:
            c = json.loads(c)
        if str(r.status)[0] == '4':
            raise HttpClientError(str(r.status), r, c)
        if model:
            if isinstance(model, list):
                creator = getattr(models, model[0])
                c = [creator(**d) for d in c]
            else:
                c = getattr(models, model)(**c)
        return r, c

    args.req_get = http_method
    args.req_post = partial(http_method, method='POST')

    # Make the repository information available, if it will be useful
    # Note: We skip this step for `show -b' for speed, see #20
    if not command == 'setup' \
        and not (command == 'show' and args.browse is True):
        try:
            r, c = args.req_get('%s/repos/%s' % (args.host_url, args.project))
        except HttpClientError as e:
            if e.content['message'] == 'Not Found':
                raise RepoError(_('Invalid project %r') % args.project)
            raise
        args.repo_obj = models.Repository(**c)
        if not args.repo_obj.has_issues:
            raise RepoError(("Issues aren't enabled for %r") % args.project)


def sync_labels(args):
    """Manage labels for a project.

    :param argparse.Namespace args: argparse namespace to operate on
    :rtype: ``list``
    :return: List of project's label names

    """
    labels_url = '%s/repos/%s/labels' % (args.host_url, args.project)
    r, c = args.req_get(labels_url)
    label_names = [label['name'] for label in c]

    for label in args.add:
        if label not in label_names:
            raise ValueError(_('No such label %r') % label)
    for label in args.create:
        if label in label_names:
            print warn(_('%r label already exists') % label)
        else:
            data = {'name': label, 'color': '000000'}
            args.req_post(labels_url, body=data)
    return label_names + args.add + args.create
