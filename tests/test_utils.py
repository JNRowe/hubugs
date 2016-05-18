#
# coding=utf-8
"""test_utils - Test utility functions"""
# Copyright © 2010-2016  James Rowe <jnrowe@gmail.com>
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

from subprocess import CalledProcessError
from unittest import TestCase

from click import BadParameter
from expecter import expect
from mock import (Mock, patch)
from nose2.tools import params

from hubugs import ProjectNameParamType
from hubugs import utils


def fake_env(key, default=None):
    """Fake environment settings used for os.getenv mocking."""
    fake_data = {
        'HUBUGS_TOKEN': 'xxx',
        'HOME': '/home/JNRowe',
        'XDG_CACHE_HOME': 'cache_dir',
    }
    return fake_data[key]


class TestProjectNameParamType(TestCase):
    @params(
        ('misc-overlay', 'JNRowe/misc-overlay'),
        ('JNRowe/misc-overlay', 'JNRowe/misc-overlay'),
        ('ask/python-github2', 'ask/python-github2'),
    )
    @patch('hubugs.utils.get_github_api')
    @patch('hubugs.utils.get_git_config_val')
    def test_repo_name(self, repo, expected, get_git_config_val,
                       get_github_api):
        get_github_api().repos.show = Mock(return_value=True)
        get_git_config_val.return_value = 'JNRowe'

        p = ProjectNameParamType()
        p.convert(repo, None, None) == expected

    @patch('hubugs.utils.get_github_api')
    @patch('hubugs.utils.get_git_config_val')
    def test_no_user(self, get_git_config_val, get_github_api):
        get_github_api().repos.show = Mock(return_value=True)
        get_git_config_val.return_value = None

        p = ProjectNameParamType()
        with expect.raises(BadParameter):
            p.convert('misc-overlay', None, None)


class GetGitConfigVal(TestCase):
    @patch('hubugs.utils.check_output')
    def test_valid_key(self, check_output):
        check_output.return_value = 'JNRowe'
        expect(utils.get_git_config_val('github.user')) == 'JNRowe'

    @patch('hubugs.utils.check_output')
    def test_invalid_key(self, check_output):
        check_output.return_value = ''
        expect(utils.get_git_config_val('no_such_key')) == ''

    @patch('hubugs.utils.check_output')
    def test_command_error(self, check_output):
        check_output.side_effect = CalledProcessError('255', 'cmd')
        expect(utils.get_git_config_val('github.user')) is None


class GetEditor(TestCase):
    def test_git_editor_envvar(self):
        with patch.dict('os.environ', {'EDITOR': 'custom git editor'},
                        clear=True):
            expect(utils.get_editor()) == ['custom', 'git', 'editor']

    def test_editor_environment_editor(self):
        with patch.dict('os.environ', {'EDITOR': 'editor'}, clear=True):
            expect(utils.get_editor()) == ['editor', ]


class GetRepo(TestCase):
    @params(
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
    )
    @patch('hubugs.utils.get_git_config_val')
    def test_repo_url(self, repo, get_git_config_val):
        # side_effect to skip hubugs.project call
        get_git_config_val.side_effect = [None, repo]
        expect(utils.get_repo()) == 'JNRowe/misc-overlay'

    @params(
        'git://github.com/misc-overlay.git',
        None,
        'http://example.com/dog.git',
    )
    @patch('hubugs.utils.get_git_config_val')
    def test_broken_url(self, repo, get_git_config_val):
        # side_effect to skip hubugs.project call
        get_git_config_val.side_effect = [None, repo]
        with expect.raises(ValueError):
            utils.get_repo()

    @patch('hubugs.utils.get_git_config_val')
    def test_config_project(self, get_git_config_val):
        # side_effect to skip hubugs.project call
        get_git_config_val.return_value = 'JNRowe/misc-overlay'
        expect(utils.get_repo()) == 'JNRowe/misc-overlay'
