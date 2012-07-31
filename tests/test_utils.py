import argparse

from subprocess import CalledProcessError
from unittest import TestCase

from expecter import expect
from mock import (Mock, patch)
from nose2.tools import params

from hubugs import utils

from utils import no_travis

# We only test forced styling output of blessings, as blessings handles the
# sys.stdout.isatty() flipping
utils.T = utils.blessings.Terminal(force_styling=True)


def fake_env(key, default=None):
    """Fake environment settings used for os.getenv mocking."""
    fake_data = {
        'HUBUGS_TOKEN': 'xxx',
        'HOME': '/home/JNRowe',
        'XDG_CACHE_HOME': 'cache_dir',
    }
    return fake_data[key]


@params(
    (utils.success, u'\x1b[38;5;10mtest\x1b[m\x1b(B'),
    (utils.fail, u'\x1b[38;5;9mtest\x1b[m\x1b(B'),
    (utils.warn, u'\x1b[38;5;11mtest\x1b[m\x1b(B'),
)
@no_travis
def test_colouriser(f, result):
    expect(f('test')) == result


class ProjectAction(TestCase):
    def setUp(self):
        self.parser = utils.argh.ArghParser('test_parser')
        # Stub out ._print_message() to stop help messages being displayed on
        # stderr during tests.
        self.parser._print_message = Mock(return_value=True)
        self.namespace = argparse.Namespace()
        self.action = utils.ProjectAction([], '')

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

        self.action(self.parser, self.namespace, repo)
        expect(self.namespace.project) == expected

    @patch('hubugs.utils.get_github_api')
    @patch('hubugs.utils.get_git_config_val')
    def test_no_user(self, get_git_config_val, get_github_api):
        get_github_api().repos.show = Mock(return_value=True)
        get_git_config_val.return_value = None
        with expect.raises(SystemExit):
            self.action(self.parser, self.namespace, 'misc-overlay')


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
        expect(utils.get_git_config_val('github.user')) == None


class GetEditor(TestCase):
    def test_git_editor_envvar(self):
        with patch.dict('os.environ', {'EDITOR': 'custom git editor'}):
            expect(utils.get_editor()) == ['custom', 'git', 'editor']

    def test_editor_environment_visual(self):
        with patch.dict('os.environ', {'VISUAL': 'visual'}):
            expect(utils.get_editor()) == ['visual', ]

    def test_editor_environment_editor(self):
        with patch.dict('os.environ', {'EDITOR': 'editor'}):
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
    )
    @patch('hubugs.utils.get_git_config_val')
    def test_repo_url(self, repo, get_git_config_val):
        get_git_config_val.return_value = repo
        expect(utils.get_repo()) == 'JNRowe/misc-overlay'

    @params(
        'git://github.com/misc-overlay.git',
        None,
        'http://example.com/dog.git',
    )
    @patch('hubugs.utils.get_git_config_val')
    def test_broken_url(self, repo, get_git_config_val):
        get_git_config_val.return_value = repo
        with expect.raises(ValueError):
            utils.get_repo()
