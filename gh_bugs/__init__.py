#! /usr/bin/python -tt
# coding=utf-8
"""gh_bugs - Simple client for GitHub issues"""
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

from . import _version


__version__ = _version.dotted
__date__ = _version.date
__author__ = "James Rowe <jnrowe@gmail.com>"
__copyright__ = "Copyright (C) 2010-2011  James Rowe <jnrowe@gmail.com>"
__license__ = "GNU General Public License Version 3"
__credits__ = ""
__history__ = "See git repository"

from email.utils import parseaddr

__doc__ += """.

``gh_bugs`` is a very simple client for working with `GitHub's issue tracker`_.

.. _GitHub's issue tracker: http://github.com/blog/411-github-issue-tracker

.. moduleauthor:: `%s <mailto:%s>`__
""" % parseaddr(__author__)

import datetime
import inspect
import operator
import os
import re
import subprocess
import sys
import tempfile

import argh
import jinja2

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

USER_DATA_DIR = os.environ.get("XDG_DATA_HOME",
                               os.path.join(os.environ.get("HOME", "/"),
                                            ".local"))
SYSTEM_DATA_DIR = os.environ.get("XDG_DATA_DIRS",
                                 "/usr/local/share/:/usr/share/").split(":")
PKG_DATA_DIRS = [os.path.join(USER_DATA_DIR, "gh_bugs", "templates"), ]
for directory in SYSTEM_DATA_DIR:
    PKG_DATA_DIRS.append(os.path.join(directory, "gh_bugs", "templates"))

ENV = jinja2.Environment(loader=jinja2.ChoiceLoader(
    [jinja2.FileSystemLoader(s) for s in PKG_DATA_DIRS]))
ENV.loader.loaders.append(jinja2.PackageLoader("gh_bugs", "templates"))
if colored and sys.stdout.isatty():
    ENV.filters["colourise"] = colored
else:
    ENV.filters["colourise"] = lambda string, *args, **kwargs: string


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
            repository = "%s/%s" % (get_git_config_val("github.user"), repository)
        namespace.repository = repository


def edit_text(edit_type="default", data=None):
    """Edit data with external editor

    :type edit_type: ``str``
    :param edit_type: Template to use in editor
    :type data: ``dict``
    :param data: Information to pass to template
    :rtype: ``str``
    :return: User supplied text
    :raise ValueError: No message given
    """
    template = ENV.get_template("edit/%s.mkd" % edit_type)
    with tempfile.NamedTemporaryFile(suffix=".mkd") as temp:
        temp.write(template.render(data if data else {}))
        temp.flush()

        subprocess.check_call([get_editor(), temp.name])

        temp.seek(0)
        text = "".join(filter(lambda s: not s.startswith("#"),
                              temp.readlines())).strip()

    if not text:
        raise ValueError("No message given")

    return text.strip()


def get_github_api():
    """Create a GitHub API instance

    :rtype: ``Github``
    :return: Authenticated GitHub API instance
    """
    user = os.getenv("GITHUB_USER", get_git_config_val("github.user"))
    token = os.getenv("GITHUB_TOKEN", get_git_config_val("github.token"))

    if "cache" in inspect.getargspec(Github.__init__).args:
        xdg_cache_dir = os.getenv("XDG_CACHE_HOME",
                                  os.path.join(os.getenv("HOME", "/"), ".cache"))
        cache_dir = os.path.join(xdg_cache_dir, "gh_bugs")
        kwargs = {"cache": cache_dir}
    else:
        kwargs = {}
    return Github(username=user, api_token=token, **kwargs)


def get_git_config_val(key, allow_fail=False):
    """Fetch a git configuration value

    :type key: ``str``
    :param key: Configuration value to fetch
    :type allow_fail: ``bool``
    :param allow_fail: Ignore errors
    :raise subprocess.CalledProcessError: If ``allow_fail`` is False, and
        command returns non-zero exit code
    """
    try:
        output = subprocess.check_output(["git", "config", key]).strip()
    except subprocess.CalledProcessError:
        if allow_fail:
            output = None
        else:
            raise
    return output


def get_editor():
    """Choose a suitable editor

    This follows the method defined in :manpage:`git-var(1)`

    :rtype: ``str``
    :return: Users chosen editor, or ``vi`` if not set"""
    # Match git for editor preferences
    editor = os.getenv("GIT_EDITOR")
    if not editor:
        editor = get_git_config_val("core.editor", allow_fail=True)
        if not editor:
            editor = os.getenv("VISUAL", os.getenv("EDITOR", "vi"))
    return editor


def get_repo():
    "Extract GitHub repository name from config"
    data = get_git_config_val("remote.origin.url", True)
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


def relative_time(timestamp):
    """Format a relative time

    Taken from bleeter_.  Duplication is evil, I know.

    :type timestamp: ``datetime.datetime``
    :param timestamp: Event to generate relative timestamp against
    :rtype: ``str``
    :return: Human readable date and time offset

    .. _bleeter: http://jnrowe.github.com/bleeter/
    """

    numstr = ". a two three four five six seven eight nine ten".split()

    matches = [
        60 * 60 * 24 * 365,
        60 * 60 * 24 * 28,
        60 * 60 * 24 * 7,
        60 * 60 * 24,
        60 * 60,
        60,
        1,
    ]
    match_names = ["year", "month", "week", "day", "hour", "minute", "second"]

    delta = datetime.datetime.now(UTC()) - timestamp
    seconds = delta.days * 86400 + delta.seconds
    for scale in matches:
        i = seconds // scale
        if i:
            name = match_names[matches.index(scale)]
            break

    if i == 1 and name in ("year", "month", "week"):
        result = "last %s" % name
    elif i == 1 and name == "day":
        result = "yesterday"
    elif i == 1 and name == "hour":
        result = "about an hour ago"
    else:
        result = "about %s %s%s ago" % (i if i > 10 else numstr[i], name,
                                        "s" if i > 1 else "")
    return result
ENV.filters["relative_time"] = relative_time


def term_markdown(text):
    """Basic Markdown text-based renderer

    Formats headings, horizontal rules and emphasis.

    :type text: ``str``
    :param text: Text to process
    :rtype: ``str``
    :return: Rendered text with terminal control sequences
    """
    if colored and sys.stdout.isatty():
        # For uniform line ending split and rejoin, this saves having to handle \r and \r\n
        text = "\n".join(text.splitlines())
        text = re.sub(r"^#+ +(.*)$",
                      lambda s: colored(s.groups()[0], attrs=["underline"]),
                      text, flags=re.MULTILINE)
        text = re.sub(r"^(([*-] *){3,})$",
                      lambda s: colored(s.groups()[0], "green"),
                      text, flags=re.MULTILINE)
        text = re.sub(r'([\*_]{2})([^ \*]+)\1',
                      lambda s: colored(s.groups()[1], attrs=["underline"]),
                      text)
        text = re.sub(r'([\*_])([^ \*]+)\1',
                      lambda s: colored(s.groups()[1], attrs=["bold"]), text)
        if sys.stdout.encoding == "UTF-8":
            text = re.sub(r"^( {0,4})[*+-] ", u"\\1• ", text,
                          flags=re.MULTILINE)

    return text
ENV.filters["term_markdown"] = term_markdown


def display_bugs(bugs, order):
    """Display bugs to users

    :type bugs: ``list` of ``github2.issues.Issue``
    :param bugs: Bugs to display
    :type order: ``str``
    :param order: Sorting order for displaying bugs
    """
    if not bugs:
        return success("No bugs found!")

    # Match ordering method to bug attribute
    if order == "priority":
        attr = "position"
    elif order == "updated":
        attr = "updated_at"
    else:
        attr = order

    bugs = sorted(bugs, key=operator.attrgetter(attr))

    columns = get_term_size()[1]

    template = ENV.get_template("view/list.txt")

    max_id = max(i.number for i in bugs)
    id_len = len(str(max_id))
    spacer = " " * (id_len - 2)

    return template.render(bugs=bugs, spacer=spacer, id_len=id_len,
                           max_title=columns - id_len - 2)


@argh.alias("list")
@argh.arg("-s", "--state", default="open", choices=["open", "closed", "all"],
          help="state of bugs to list")
@argh.arg("-l", "--label", help="list bugs with specified label",
          metavar="label")
@argh.arg("-o", "--order", default="number",
          choices=["number", "priority", "updated", "votes"],
          help="Sort order for listing bugs")
def list_bugs(args):
    "listing bugs"
    github = get_github_api()
    states = ["open", "closed"] if args.state == "all" else [args.state, ]
    bugs = []
    for state in states:
        bugs.extend(github.issues.list(args.repository, state))
    return display_bugs(bugs, args.order)


@argh.arg("-s", "--state", default="open", choices=["open", "closed", "all"],
          help="state of bugs to search")
@argh.arg("-o", "--order", default="number",
          choices=["number", "priority", "updated", "votes"],
          help="Sort order for listing bugs")
@argh.arg("term", help="term to search bugs for")
def search(args):
    "searching bugs"
    github = get_github_api()
    states = ["open", "closed"] if args.state == "all" else [args.state, ]
    bugs = []
    for state in states:
        bugs.extend(github.issues.search(args.repository, args.term, state))
    return display_bugs(bugs, args.order)


@argh.arg("-f", "--full", default=False, help="show bug including comments")
@argh.arg("bugs", nargs="+", type=int, help="bug number(s) to operate on")
def show(args):
    "displaying bugs"
    github = get_github_api()
    template = ENV.get_template("view/issue.txt")
    for bug_no in args.bugs:
        try:
            bug = github.issues.show(args.repository, bug_no)
        except RuntimeError as e:
            if "Issue #%s not found" % bug_no in e.args[0]:
                yield fail("Issue %r not found" % bug_no)
            else:
                raise

        if args.full:
            comments = github.issues.comments(args.repository, bug.number)
        else:
            comments = []
        yield template.render(bug=bug, comments=comments, full=True)


@argh.alias("open")
@argh.arg("title", help="title for the new bug", nargs="?")
@argh.arg("body", help="body for the new bug", nargs="?")
def open_bug(args):
    "opening new bugs"
    github = get_github_api()
    if not args.title:
        text = edit_text("open").splitlines()
        title = text[0]
        body = "\n".join(text[1:])
    else:
        title = args.title
        body = args.body
    bug = github.issues.open(args.repository, title, body)
    return success("Bug %d opened" % bug.number)


@argh.arg("-m", "--message", help="comment text")
@argh.arg("bugs", nargs="+", type=int, help="bug number(s) to operate on")
def comment(args):
    "commenting on bugs"
    github = get_github_api()
    if not args.message:
        message = edit_text()
    else:
        message = args.message
    for bug in args.bugs:
        try:
            github.issues.comment(args.repository, bug, message)
        except RuntimeError as e:
            if "Issue #%s not found" % bug in e.args[0]:
                yield fail("Issue %r not found" % bug)
            else:
                raise


@argh.arg("title", help="title for the new bug", nargs="?")
@argh.arg("body", help="body for the new bug", nargs="?")
@argh.arg("bugs", nargs="+", type=int, help="bug number(s) to operate on")
def edit(args):
    "editing bugs"
    github = get_github_api()
    for bug in args.bugs:
        if not args.title:
            try:
                current = github.issues.show(args.repository, bug)
            except RuntimeError as e:
                if "Issue #%s not found" % bug in e.args[0]:
                    yield fail("Issue %r not found" % bug)
                    continue
                else:
                    raise
            current_data = {"title": current.title, "body": current.body}
            text = edit_text("open", current_data).splitlines()
            title = text[0]
            body = "\n".join(text[1:])
        else:
            title = args.title
            body = args.body

        try:
            github.issues.edit(args.repository, bug, title, body)
        except RuntimeError as e:
            if "Issue #%s not found" % bug in e.args[0]:
                yield fail("Issue %r not found" % bug)
            else:
                raise


@argh.arg("-m", "--message", help="comment text")
@argh.arg("bugs", nargs="+", type=int, help="bug number(s) to operate on")
def close(args):
    "closing bugs"
    github = get_github_api()
    if not args.message:
        try:
            message = edit_text()
        except ValueError:
            # Message isn't required for closing, but it is good practice
            message = None
    else:
        message = args.message
    for bug in args.bugs:
        try:
            if message:
                github.issues.comment(args.repository, bug, message)
            github.issues.close(args.repository, bug)
        except RuntimeError as e:
            if "Issue #%s not found" % bug in e.args[0]:
                yield fail("Issue %r not found" % bug)
            else:
                raise


@argh.arg("-m", "--message", help="comment text")
@argh.arg("bugs", nargs="+", type=int, help="bug number(s) to operate on")
def reopen(args):
    "reopening closed bugs"
    github = get_github_api()
    if not args.message:
        try:
            message = edit_text()
        except ValueError:
            # Message isn't required for reopening, but it is good practice
            message = None
    else:
        message = args.message
    for bug in args.bugs:
        try:
            if message:
                github.issues.comment(args.repository, bug, message)
            github.issues.reopen(args.repository, bug)
        except RuntimeError as e:
            if "Issue #%s not found" % bug in e.args[0]:
                yield fail("Issue %r not found" % bug)
            else:
                raise


@argh.arg("-a", "--add", action="append", default=[],
          help="add label to issue", metavar="label")
@argh.arg("-r", "--remove", action="append", default=[],
          help="remove label from issue", metavar="label")
@argh.arg("bugs", nargs="+", type=int, help="bug number(s) to operate on")
def label(args):
    "labelling bugs"
    github = get_github_api()
    for bug in args.bugs:
        try:
            for label in args.add:
                github.issues.add_label(args.repository, bug, label)
            for label in args.remove:
                github.issues.remove_label(args.repository, bug, label)
        except RuntimeError as e:
            if "Issue #%s not found" % bug in e.args[0]:
                yield fail("Issue %r not found" % bug)
            else:
                raise


def main():
    """Main script"""
    parser = argh.ArghParser(description=__doc__.splitlines()[0],
                             epilog="Please report bugs to the JNRowe/gh_bugs" \
                                    " repository or by email to %s" % __author__,
                             version="%%(prog)s %s" % __version__)
    parser.add_argument("-r", "--repository", action=RepoAction,
                        default=get_repo(),
                        help="GitHub repository to operate on",
                        metavar="repo")
    parser.add_commands([list_bugs, search, show, open_bug, comment, edit,
                         close, reopen, label])
    try:
        parser.dispatch()
    except RuntimeError as e:
        if "Repository not found" in e.args[0]:
            print fail("Repository %r not found" % get_repo())
        else:
            raise

if __name__ == '__main__':
    main()
