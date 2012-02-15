import argparse

from subprocess import CalledProcessError
from unittest import TestCase

from mock import (Mock, patch)
from nose.tools import (assert_equals, raises)

from hubugs import utils


# We only test forced styling output of blessings, as blessings handles the
# sys.stdout.isatty() flipping
utils.T = utils.blessings.Terminal(force_styling=True)


def fake_env(key, default=None):
    """Fake environment settings used for os.getenv mocking"""
    fake_data = {
        'GITHUB_USER': 'JNRowe',
        'GITHUB_TOKEN': 'xxx',
        'HOME': '/home/JNRowe',
        'XDG_CACHE_HOME': 'cache_dir',
    }
    return fake_data[key]


class Colouriser(TestCase):
    def test_colouriser(self):
        assert_equals(utils.success('test'), u'\x1b[38;5;10mtest\x1b[m\x1b(B')
        assert_equals(utils.fail('test'), u'\x1b[38;5;9mtest\x1b[m\x1b(B')
        assert_equals(utils.warn('test'), u'\x1b[38;5;11mtest\x1b[m\x1b(B')


class ProjectAction(TestCase):
    def setUp(self):
        self.parser = utils.argh.ArghParser('test_parser')
        # Stub out ._print_message() to stop help messages being displayed on
        # stderr during tests.
        self.parser._print_message = Mock(return_value=True)
        self.namespace = argparse.Namespace()
        self.action = utils.ProjectAction([], '')

    @patch('hubugs.utils.get_github_api')
    @patch('hubugs.utils.get_git_config_val')
    def test_repo_name(self, get_git_config_val, get_github_api):
        get_github_api().repos.show = Mock(return_value=True)
        get_git_config_val.return_value = 'JNRowe'

        self.action(self.parser, self.namespace, 'misc-overlay')
        assert_equals(self.namespace.project, 'JNRowe/misc-overlay')

        self.action(self.parser, self.namespace, 'JNRowe/misc-overlay')
        assert_equals(self.namespace.project, 'JNRowe/misc-overlay')

        self.action(self.parser, self.namespace, 'ask/python-github2')
        assert_equals(self.namespace.project, 'ask/python-github2')

    @patch('hubugs.utils.get_github_api')
    @patch('hubugs.utils.get_git_config_val')
    @raises(SystemExit)
    def test_no_user(self, get_git_config_val, get_github_api):
        get_github_api().repos.show = Mock(return_value=True)
        get_git_config_val.return_value = None
        self.action(self.parser, self.namespace, 'misc-overlay')


class GetGithubApi(TestCase):
    @patch('os.getenv')
    @patch('os.mkdir')
    def test_api_builder(self, mkdir, getenv):
        mkdir.return_value = True
        getenv.side_effect = fake_env
        api = utils.get_github_api()
        assert_equals(api.request.username, 'JNRowe')
        assert_equals(api.request.api_token, 'xxx')
        assert_equals(api.request._http.cache.cache, 'cache_dir/hubugs')

    @patch('os.getenv')
    @raises(EnvironmentError)
    def test_invalid_auth(self, getenv):
        getenv.return_value = None
        utils.get_github_api()


class GetGitConfigVal(TestCase):
    @patch('hubugs.utils.check_output')
    def test_valid_key(self, check_output):
        check_output.return_value = 'JNRowe'
        assert_equals(utils.get_git_config_val('github.user'), 'JNRowe')

    @patch('hubugs.utils.check_output')
    def test_invalid_key(self, check_output):
        check_output.return_value = ''
        assert_equals(utils.get_git_config_val('no_such_key'), '')

    @patch('hubugs.utils.check_output')
    def test_command_error(self, check_output):
        check_output.side_effect = CalledProcessError('255', 'cmd')
        assert_equals(utils.get_git_config_val('github.user'), None)


class GetEditor(TestCase):
    @patch('os.getenv')
    def test_git_editor_envvar(self, getenv):
        getenv.return_value = 'custom git editor'
        assert_equals(utils.get_editor(), 'custom git editor')

    @patch('hubugs.utils.get_git_config_val')
    @patch('os.getenv')
    def test_git_editor_config(self, getenv, get_git_config_val):
        getenv.return_value = None
        get_git_config_val.return_value = 'custom config editor'
        assert_equals(utils.get_editor(), 'custom config editor')

    @patch('hubugs.utils.get_git_config_val')
    @patch('os.getenv')
    def test_editor_environment_visual(self, getenv, get_git_config_val):
        def fake_env(key, default=None):
            return {'VISUAL': 'visual'}.get(key)
        getenv.side_effect = fake_env
        get_git_config_val.return_value = None
        assert_equals(utils.get_editor(), 'visual')

    @patch('hubugs.utils.get_git_config_val')
    @patch('os.getenv')
    def test_editor_environment_editor(self, getenv, get_git_config_val):
        def fake_env(key, default=None):
            return {'EDITOR': 'editor'}.get(key, default)
        getenv.side_effect = fake_env
        get_git_config_val.return_value = None
        assert_equals(utils.get_editor(), 'editor')

    @patch('hubugs.utils.get_git_config_val')
    @patch('os.getenv')
    def test_editor_default(self, getenv, get_git_config_val):
        def fake_env(key, default=None):
            return default
        getenv.side_effect = fake_env
        get_git_config_val.return_value = None
        assert_equals(utils.get_editor(), 'vi')


class GetRepo(TestCase):
    @patch('hubugs.utils.get_git_config_val')
    def test_ssh_url(self, get_git_config_val):
        get_git_config_val.return_value = \
            'git@github.com:JNRowe/misc-overlay.git'
        assert_equals(utils.get_repo(), 'JNRowe/misc-overlay')

    @patch('hubugs.utils.get_git_config_val')
    def test_ssh_url_no_suffix(self, get_git_config_val):
        get_git_config_val.return_value = \
            'git@github.com:JNRowe/misc-overlay'
        assert_equals(utils.get_repo(), 'JNRowe/misc-overlay')

    @patch('hubugs.utils.get_git_config_val')
    def test_git_url(self, get_git_config_val):
        get_git_config_val.return_value = \
            'git://github.com/JNRowe/misc-overlay.git'
        assert_equals(utils.get_repo(), 'JNRowe/misc-overlay')

    @patch('hubugs.utils.get_git_config_val')
    def test_git_url_no_suffix(self, get_git_config_val):
        get_git_config_val.return_value = \
            'git://github.com/JNRowe/misc-overlay'
        assert_equals(utils.get_repo(), 'JNRowe/misc-overlay')

    @patch('hubugs.utils.get_git_config_val')
    def test_https_url(self, get_git_config_val):
        get_git_config_val.return_value = \
            'https://JNRowe@github.com/JNRowe/misc-overlay.git'
        assert_equals(utils.get_repo(), 'JNRowe/misc-overlay')

    @patch('hubugs.utils.get_git_config_val')
    def test_https_url_no_suffix(self, get_git_config_val):
        get_git_config_val.return_value = \
            'https://JNRowe@github.com/JNRowe/misc-overlay'
        assert_equals(utils.get_repo(), 'JNRowe/misc-overlay')

    @patch('hubugs.utils.get_git_config_val')
    def test_http_url(self, get_git_config_val):
        get_git_config_val.return_value = \
            'http://JNRowe@github.com/JNRowe/misc-overlay.git'
        assert_equals(utils.get_repo(), 'JNRowe/misc-overlay')

    @patch('hubugs.utils.get_git_config_val')
    def test_http_url_no_suffix(self, get_git_config_val):
        get_git_config_val.return_value = \
            'http://JNRowe@github.com/JNRowe/misc-overlay'
        assert_equals(utils.get_repo(), 'JNRowe/misc-overlay')

    @patch('hubugs.utils.get_git_config_val')
    def test_http_url_no_auth(self, get_git_config_val):
        get_git_config_val.return_value = \
            'http://github.com/JNRowe/misc-overlay.git'
        assert_equals(utils.get_repo(), 'JNRowe/misc-overlay')

    @patch('hubugs.utils.get_git_config_val')
    def test_http_url_no_suffix_no_auth(self, get_git_config_val):
        get_git_config_val.return_value = \
            'http://github.com/JNRowe/misc-overlay'
        assert_equals(utils.get_repo(), 'JNRowe/misc-overlay')

    @patch('hubugs.utils.get_git_config_val')
    @raises(ValueError)
    def test_broken_url(self, get_git_config_val):
        get_git_config_val.return_value = 'git://github.com/misc-overlay.git'
        utils.get_repo()

    @patch('hubugs.utils.get_git_config_val')
    @raises(ValueError)
    def test_no_url(self, get_git_config_val):
        get_git_config_val.return_value = None
        utils.get_repo()

    @patch('hubugs.utils.get_git_config_val')
    @raises(ValueError)
    def test_invalid_url(self, get_git_config_val):
        get_git_config_val.return_value = 'http://example.com/dog.git'
        utils.get_repo()


@patch('hubugs.utils.check_output')
def test_get_term_size(check_output):
    check_output.return_value = '62 118'
    term = utils.get_term_size()
    assert_equals(term.lines, 62)
    assert_equals(term.columns, 118)


class SetApi(TestCase):
    @patch('os.getenv')
    @patch('hubugs.utils.get_repo')
    def test_no_project(self, get_repo, getenv):
        get_repo.return_value = 'JNRowe/misc-overlay'
        getenv.side_effect = fake_env
        namespace = argparse.Namespace(project=None, host_url=None)
        utils.set_api(namespace)
        assert_equals(namespace.project, 'JNRowe/misc-overlay')

    @patch('os.getenv')
    def test_project(self, getenv):
        getenv.side_effect = fake_env
        namespace = argparse.Namespace(project='JNRowe/misc-overlay',
                                       host_url=None)
        utils.set_api(namespace)
        assert_equals(namespace.project, 'JNRowe/misc-overlay')

    @patch('os.getenv')
    @patch('github2.request.GithubRequest.raw_request')
    def test_api(self, raw_request, getenv):
        raw_request.return_value = {u'issues': []}
        getenv.side_effect = fake_env
        namespace = argparse.Namespace(project='JNRowe/misc-overlay',
                                       host_url=None)
        utils.set_api(namespace)
        assert_equals(namespace.api('list'), [])
