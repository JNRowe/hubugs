#
# coding=utf-8
"""utils - Utility functions for hubugs"""
# Copyright (C) 2010-2011  James Rowe <jnrowe@gmail.com>
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

import inspect
import os
import re
import subprocess
import sys

from collections import namedtuple
from functools import partial

import argh
import httplib2

from github2 import core as ghcore
from github2.client import Github

try:
    from termcolor import colored
except ImportError:  # pragma: no cover
    colored = None  # pylint: disable-msg=C0103


# Set up informational message functions
def _colourise(text, colour):
    """Colour text, if possible

    :param str text: Text to colourise
    :param str colour:
    :rtype: str
    :return: Colourised text, if possible
    """
    return colored(text, colour) if colored and sys.stdout.isatty() else text
# pylint: disable-msg=C0103
success = partial(_colourise, colour='green')
fail = partial(_colourise, colour='red')
warn = partial(_colourise, colour='yellow')
# pylint: enable-msg=C0103


# Use timezone aware datetimes in github2 package
ghcore.NAIVE = False


class ProjectAction(argh.utils.argparse.Action):
    """argparse action class for setting project"""
    def __call__(self, parser, namespace, project, option_string=None):
        "Set fully qualified GitHub project name"
        if not "/" in project:
            user = os.getenv("GITHUB_USER", get_git_config_val("github.user"))
            if not user:
                raise parser.error("No GitHub user setting!")
            project = "%s/%s" % (user, project)
        try:
            # Check for project validity early on.  This check is normally less
            # than a 500 bytes transfer
            get_github_api().repos.show(project)
        except RuntimeError as error:
            if "Repository not found" in error.args[0]:
                raise parser.error(fail("Project %r not found" % project))
            else:
                raise
        except httplib2.ServerNotFoundError:
            raise parser.error(fail("Project lookup failed.  Network or "
                                    "GitHub down?"))
        except EnvironmentError as error:
            raise parser.error(error.args[0])

        namespace.project = project


def check_output(args):
    """Simple check_output implementation for Python 2.6 compatibililty

    :param list args: Command and arguments to call
    :rtype: str:
    :return: Command output
    :raise subprocess.CalledProcessError: If command execution fails
    """
    try:
        return subprocess.check_output(args)
    except AttributeError:
        process = subprocess.Popen(args, stdout=subprocess.PIPE)
        output, unused_err = process.communicate()
        retcode = process.poll()
        if retcode:
            raise subprocess.CalledProcessError(retcode, args[0])
        return output


def get_github_api():
    """Create a GitHub API instance

    :rtype: ``Github``
    :return: Authenticated GitHub API instance
    """
    user = os.getenv("GITHUB_USER", get_git_config_val("github.user"))
    token = os.getenv("GITHUB_TOKEN", get_git_config_val("github.token"))
    if not user or not token:
        raise EnvironmentError("No GitHub authentication settings found!")

    if "cache" in inspect.getargspec(Github.__init__).args:
        xdg_cache_dir = os.getenv("XDG_CACHE_HOME",
                                  os.path.join(os.getenv("HOME", "/"),
                                               ".cache"))
        cache_dir = os.path.join(xdg_cache_dir, "hubugs")
        kwargs = {"cache": cache_dir}
    else:
        kwargs = {}
    return Github(username=user, api_token=token, **kwargs)


def get_git_config_val(key, default=None):
    """Fetch a git configuration value

    :param str key: Configuration value to fetch
    """
    try:
        output = check_output(["git", "config", key]).strip()
    except subprocess.CalledProcessError:
        output = default
    return output


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
    data = get_git_config_val("remote.origin.url")
    if not data:
        raise ValueError("No `origin' remote found")
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
        raise ValueError("Unknown project")


def get_term_size():
    """Fetch the current terminal size

    :rtype: ``namedtuple``
    :return: Number of lines and columns in current terminal
    """
    lines, columns = map(int, check_output(["stty", "size"]).split())
    return namedtuple('Tty', 'lines columns')(lines, columns)


def set_api(args):
    """Add authenticated issues API object to args namespace

    :param argparse.Namespace args: argparse namespace to operate on
    """
    if not args.project:
        args.project = get_repo()
    api = get_github_api()
    issues = api.issues

    def api_method(method, *opts, **kwargs):
        "Wrapper for calling functions from api.issues"
        return getattr(issues, method)(args.project, *opts, **kwargs)
    args.api = api_method
    # Include a direct httplib2.Http object, for non-issues related network
    # access.
    args._http = api.request._http
