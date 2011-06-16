import imp
import sys

from unittest import TestCase

from mock import (Mock, patch)
from nose.tools import (assert_equals, assert_false)

from gh_bugs import utils


class Colouriser(TestCase):
    @patch('sys.stdout')
    def test_is_not_a_tty_colour(self, stdout):
        stdout.isatty = Mock(return_value=False)
        assert_false(sys.stdout.isatty())
        assert_equals(utils.success('test'), 'test')
        assert_equals(utils.fail('test'), 'test')
        assert_equals(utils.warn('test'), 'test')

    @patch('sys.stdout')
    def test_colouriser(self, stdout):
        stdout.isatty = Mock(return_value=True)

        # This horrific-ness is here as the .isatty() test happens at import
        # time, so we need to re-import for tests.
        utils_file = open('gh_bugs/utils.py')
        new_utils = imp.load_module("new_utils", utils_file, utils_file.name,
                           (".py", utils_file.mode, imp.PY_SOURCE))

        assert_equals(new_utils.success('test'), '\x1b[32mtest\x1b[0m')
        assert_equals(new_utils.fail('test'), '\x1b[31mtest\x1b[0m')
        assert_equals(new_utils.warn('test'), '\x1b[33mtest\x1b[0m')
        del sys.modules['new_utils']
