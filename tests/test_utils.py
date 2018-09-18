#
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

from click import BadParameter
from mock import (Mock, patch)
from pytest import mark, raises

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


@mark.parametrize('repo, expected', [
    ('misc-overlay', 'JNRowe/misc-overlay'),
    ('JNRowe/misc-overlay', 'JNRowe/misc-overlay'),
    ('ask/python-github2', 'ask/python-github2'),
])
def test_ProjectNameParamType_repo_name(repo, expected):
    with patch('hubugs.utils.get_github_api') as get_github_api, \
         patch('hubugs.utils.get_git_config_val') as get_git_config_val:
        get_github_api().repos.show = Mock(return_value=True)
        get_git_config_val.return_value = 'JNRowe'

        p = ProjectNameParamType()
        p.convert(repo, None, None) == expected


def test_ProjectNameParamType_no_user():
    with patch('hubugs.utils.get_github_api') as get_github_api, \
         patch('hubugs.utils.get_git_config_val') as get_git_config_val:
        get_github_api().repos.show = Mock(return_value=True)
        get_git_config_val.return_value = None

        p = ProjectNameParamType()
        with raises(BadParameter):
            p.convert('misc-overlay', None, None)


def test_GetGitConfigVal_valid_key():
    with patch('subprocess.check_output') as check_output:
        check_output.return_value = 'JNRowe'

        assert utils.get_git_config_val('github.user') == 'JNRowe'


def test_GetGitConfigVal_invalid_key():
    with patch('subprocess.check_output') as check_output:
        check_output.return_value = ''

        assert utils.get_git_config_val('no_such_key') == ''


def test_GetGitConfigVal_command_error():
    with patch('subprocess.check_output') as check_output:
        check_output.side_effect = CalledProcessError('255', 'cmd')

        assert utils.get_git_config_val('github.user') is None


def test_GetEditor_git_editor_envvar():
    with patch.dict('os.environ', {'EDITOR': 'custom git editor'},
                    clear=True):
        assert utils.get_editor() == ['custom', 'git', 'editor']


def test_GetEditor_editor_environment_editor():
    with patch.dict('os.environ', {'EDITOR': 'editor'}, clear=True):
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
def test_GetRepo_repo_url(repo):
    with patch('hubugs.utils.get_git_config_val') as get_git_config_val:
        # side_effect to skip hubugs.project call
        get_git_config_val.side_effect = [None, repo]

        assert utils.get_repo() == 'JNRowe/misc-overlay'


@mark.parametrize('repo', [
    'git://github.com/misc-overlay.git',
    None,
    'http://example.com/dog.git',
])
def test_GetRepo_broken_url(repo):
    with patch('hubugs.utils.get_git_config_val') as get_git_config_val:
        # side_effect to skip hubugs.project call
        get_git_config_val.side_effect = [None, repo]

        with raises(ValueError):
            utils.get_repo()


def test_GetRepo_config_project():
    with patch('hubugs.utils.get_git_config_val') as get_git_config_val:
        # side_effect to skip hubugs.project call
        get_git_config_val.return_value = 'JNRowe/misc-overlay'

        assert utils.get_repo() == 'JNRowe/misc-overlay'
