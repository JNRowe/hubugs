#
"""test_utils - Test utility functions."""
# Copyright © 2011-2018  James Rowe <jnrowe@gmail.com>
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

from subprocess import CalledProcessError
from typing import Optional

from click import BadParameter
from pytest import mark, raises

from hubugs import ProjectNameParamType
from hubugs import utils


@mark.parametrize('repo, expected', [
    ('misc-overlay', 'JNRowe/misc-overlay'),
    ('JNRowe/misc-overlay', 'JNRowe/misc-overlay'),
    ('ask/python-github2', 'ask/python-github2'),
])
def test_ProjectNameParamType_repo_name(repo: str, expected: str, monkeypatch):
    monkeypatch.setattr(
        'hubugs.utils.get_github_api',
        lambda: utils.AttrDict(repos=utils.AttrDict(show=lambda: True)))
    monkeypatch.setattr('hubugs.utils.get_git_config_val', lambda _: 'JNRowe')

    p = ProjectNameParamType()
    p.convert(repo, None, None) == expected


def test_ProjectNameParamType_no_user(monkeypatch):
    monkeypatch.setattr(
        'hubugs.utils.get_github_api',
        lambda: utils.AttrDict(repos=utils.AttrDict(show=lambda: True)))
    monkeypatch.setattr('hubugs.utils.get_git_config_val', lambda _: None)

    p = ProjectNameParamType()
    with raises(BadParameter):
        p.convert('misc-overlay', None, None)


def test_GetGitConfigVal_valid_key(monkeypatch):
    monkeypatch.setattr('subprocess.check_output',
                        lambda *args, **kwargs: b'JNRowe')

    assert utils.get_git_config_val('github.user') == 'JNRowe'


def test_GetGitConfigVal_invalid_key(monkeypatch):
    monkeypatch.setattr('subprocess.check_output', lambda *args, **kwargs: b'')

    assert utils.get_git_config_val('no_such_key') == ''


def test_GetGitConfigVal_command_error(monkeypatch):
    def raise_error(*args, **kwargs):
        raise CalledProcessError('255', 'cmd')
    monkeypatch.setattr('subprocess.check_output', raise_error)

    assert utils.get_git_config_val('github.user') is None


def test_GetEditor_git_editor_envvar(monkeypatch):
    monkeypatch.setenv('EDITOR', 'custom git editor')
    assert utils.get_editor() == ['custom', 'git', 'editor']


def test_GetEditor_editor_environment_editor(monkeypatch):
    monkeypatch.setenv('EDITOR', 'editor')
    assert utils.get_editor() == ['editor', ]


@mark.parametrize('repo', [
    'git@github.com:JNRowe/misc-overlay.git',
    'git@github.com:JNRowe/misc-overlay',
    'git://github.com/JNRowe/misc-overlay.git',
    'git://github.com/JNRowe/misc-overlay',
    'https://JNRowe@github.com/JNRowe/misc-overlay.git',
    'https://JNRowe@github.com/JNRowe/misc-overlay',
    'http://JNRowe@github.com/JNRowe/misc-overlay.git',
    'http://JNRowe@github.com/JNRowe/misc-overlay',
    'http://github.com/JNRowe/misc-overlay.git',
    'http://github.com/JNRowe/misc-overlay',

    # hg-git
    'git+ssh://git@github.com:JNRowe/misc-overlay.git',
])
def test_GetRepo_repo_url(repo: str, monkeypatch):
    # side_effect to skip hubugs.project call
    results = [repo, None]
    monkeypatch.setattr('hubugs.utils.get_git_config_val',
                        lambda *args, **kwargs: results.pop())

    assert utils.get_repo() == 'JNRowe/misc-overlay'


@mark.parametrize('repo', [
    'git://github.com/misc-overlay.git',
    None,
    'http://example.com/dog.git',
])
def test_GetRepo_broken_url(repo: Optional[str], monkeypatch):
    # side_effect to skip hubugs.project call
    results = [repo, None]
    monkeypatch.setattr('hubugs.utils.get_git_config_val',
                        lambda *args, **kwargs: results.pop())

    with raises(ValueError):
        utils.get_repo()


def test_GetRepo_config_project(monkeypatch):
    monkeypatch.setattr('hubugs.utils.get_git_config_val',
                        lambda *args, **kwargs: 'JNRowe/misc-overlay')

    assert utils.get_repo() == 'JNRowe/misc-overlay'
