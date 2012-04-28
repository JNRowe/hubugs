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

from functools import partial

import argh
import blessings
import requests

from . import (_version, models)


T = blessings.Terminal()


# Set up informational message functions
def _colourise(text, colour):
    """Colour text, if possible

    :param str text: Text to colourise
    :param str colour: Colour to display text in
    :rtype: str
    :return: Colourised text, if possible
    """
    return getattr(T, colour.replace(' ', '_'))(text)


def success(text):
    return _colourise(text, 'bright green')


def fail(text):
    return _colourise(text, 'bright red')


def warn(text):
    return _colourise(text, 'bright yellow')


class RepoError(ValueError):
    """Error raised for invalid repository values"""


class ProjectAction(argh.utils.argparse.Action):
    """argparse action class for setting project"""
    def __call__(self, parser, namespace, project, option_string=None):
        "Set fully qualified GitHub project name"
        if not "/" in project:
            user = os.getenv("GITHUB_USER", get_git_config_val("github.user"))
            if not user:
                raise parser.error("No GitHub user setting!")
            project = "%s/%s" % (user, project)
        namespace.project = project


def check_output(args, **kwargs):
    """Simple check_output implementation for Python 2.6 compatibililty

    :param list args: Command and arguments to call
    :rtype: str:
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


def get_github_api(auth=True):
    """Create a GitHub API instance

    :param bool auth: Whether to create an authorised session
    :rtype: ``requests.sessions.Session``
    :return: GitHub HTTP session
    """

    def from_json(r):
        r.json = json.loads(r.text)

    def to_json(r):
        r['data'] = json.dumps(r['data'])

    headers = {
        'Accept': 'application/vnd.github.beta.full+json',
        'User-Agent': 'hubugs/%s' % _version.dotted,
    }
    if auth:
        token = os.getenv("HUBUGS_TOKEN", get_git_config_val("hubugs.token"))
        if not token:
            raise EnvironmentError("No hubugs authorisation token found!  "
                                   "Run 'hubugs setup' to create a token")
        headers["Authorization"] = "token %s" % token

    # if sys.platform == 'darwin':
    #     user_cache_dir = os.path.expanduser("~/Library/Caches")
    # else:
    #     user_cache_dir = os.path.join(os.getenv("HOME", "/"), ".cache")
    # xdg_cache_dir = os.getenv("XDG_CACHE_HOME")
    # cache_dir = os.path.join(xdg_cache_dir or user_cache_dir, "hubugs")

    # We have to invert the default cert selection behaviour, as requests
    # ignores the system configuration out of the box.  Shouldn't have to
    # resort to this, but…
    certs = requests.utils.get_os_ca_bundle_path() \
        or requests.utils.CERTIFI_BUNDLE_PATH

    return requests.session(headers=headers, verify=certs,
                            hooks={'args': to_json, 'response': from_json},
                            config={'danger_mode': True})


def get_git_config_val(key, default=None, local_only=False):
    """Fetch a git configuration value

    :param str key: Configuration value to fetch
    :param str default: Default value to use, if key isn't set
    :param bool local_only: Fetch configuration values from repo config only
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
    """Set a git configuration value

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
    """Choose a suitable editor

    This follows the method defined in :manpage:`git-var(1)`

    :rtype: ``str``
    :return: Users chosen editor, or ``vi`` if not set"""
    # Match git for editor preferences
    editor = os.getenv("GIT_EDITOR")
    if not editor:
        editor = get_git_config_val("core.editor")
        if not editor:
            editor = os.getenv("VISUAL", os.getenv("EDITOR", "vi"))
    return editor


def get_repo():
    "Extract GitHub project name from config"
    data = get_git_config_val("remote.origin.url", local_only=True)
    if not data:
        raise RepoError("No `origin' remote found")
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
        raise RepoError("Unknown project, specify with `--project' option")


def setup_environment(args):
    """Configure execution environment for commands dispatch

    :param argparse.Namespace args: argparse namespace to operate on
    """
    if not args.project:
        args.project = get_repo()

    command = args.function.__name__

    # We use manual auth when calling setup
    use_auth = not command == 'setup'
    session = get_github_api(use_auth)

    def api_method(method, loc, *pargs, **kwargs):
        func = getattr(session, method)
        url = '%s/repos/%s/issues%s%s' % (args.host_url, args.project,
                                          '/' if loc else '', loc)
        return func(url, *pargs, **kwargs)

    args.req_get = partial(api_method, 'get')
    args.req_post = partial(api_method, 'post')
    args.req_patch = partial(api_method, 'patch')
    args.req_delete = partial(api_method, 'delete')
    # Include a direct session object, for non-issues related network access.
    args.session = session

    # Make the repository information available, if it will be useful
    # Note: We skip this step for `show -b' for speed, see #20
    if not command == 'setup' \
        and not (command == 'show' and args.browse == True):
        try:
            r = session.get('%s/repos/%s' % (args.host_url, args.project))
            args.repo_obj = models.Repository.from_dict(r.json)
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                raise RepoError('Invalid project %r' % args.project)
            raise
        if not args.repo_obj.has_issues:
            raise RepoError("Issues aren't enabled for %r" % args.project)
