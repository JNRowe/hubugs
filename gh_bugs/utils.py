#
# coding=utf-8
"""utils - Utility functions for gh_bugs"""
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

import datetime
import inspect
import os
import re
import subprocess
import sys

import argh
import httplib2

from github2.client import Github

try:
    from termcolor import colored
except ImportError:  # pragma: no cover
    colored = None  # pylint: disable-msg=C0103

# Select colours if terminal is a tty
# pylint: disable-msg=C0103
if colored and sys.stdout.isatty():
    success = lambda s: colored(s, "green")
    fail = lambda s: colored(s, "red")
    warn = lambda s: colored(s, "yellow")
else:  # pragma: no cover
    success = fail = warn = str
# pylint: enable-msg=C0103


class UTC(datetime.tzinfo):
    """UTC"""

    def utcoffset(self, timestamp):
        return datetime.timedelta(0)

    def tzname(self, timestamp):
        return "UTC"

    def dst(self, timestamp):
        return datetime.timedelta(0)


class RepoAction(argh.utils.argparse.Action):
    """argparse action class for setting repository"""
    def __call__(self, parser, namespace, repository, option_string=None):
        "Set fully qualified GitHub repository name"
        if not "/" in repository:
            user = os.getenv("GITHUB_USER", get_git_config_val("github.user"))
            if not user:
                raise parser.error("No GitHub user setting!")
            repository = "%s/%s" % (user, repository)
        try:
            # Check for repo validity early on.  This check is normally less
            # than a 500 bytes transfer
            get_github_api().repos.show(repository)
        except RuntimeError as e:
            if "Repository not found" in e.args[0]:
                raise parser.error(fail("Repository %r not found" % repository))
            else:
                raise
        except httplib2.ServerNotFoundError:
            raise parser.error(fail("Repository lookup failed.  Network or "
                                    "GitHub down?"))
        except EnvironmentError as e:
            raise parser.error(e.args[0])

        namespace.repository = repository


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
                                  os.path.join(os.getenv("HOME", "/"), ".cache"))
        cache_dir = os.path.join(xdg_cache_dir, "gh_bugs")
        kwargs = {"cache": cache_dir}
    else:
        kwargs = {}
    return Github(username=user, api_token=token, **kwargs)


def get_git_config_val(key):
    """Fetch a git configuration value

    :type key: ``str``
    :param key: Configuration value to fetch
    """
    try:
        output = subprocess.check_output(["git", "config", key]).strip()
    except subprocess.CalledProcessError:
        output = None
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
    "Extract GitHub repository name from config"
    data = get_git_config_val("remote.origin.url")
    match = re.search(r"github.com[:/](.*).git", data)
    if match:
        return match.groups()[0]
    else:
        raise ValueError("Unknown repository")


def get_term_size():
    """Fetch the current terminal size

    :rtype: ``list`` of ``int``
    :return: Number of columns and lines in current terminal
    """
    return map(int, subprocess.check_output(["stty", "size"]).split())

def set_api(args):
    """Add authenticated issues API object to args namespace

    :type args: argparse.Namespace
    :param args: argparse namespace to operate on
    """
    issues = get_github_api().issues
    def api_method(method, *opts, **kwargs):
        return getattr(issues, method)(args.repository, *opts, **kwargs)
    args.api = api_method
