from collections import namedtuple
from unittest import TestCase

from mock import (Mock, patch)
from nose.tools import (assert_equals, assert_true)
from pygments import (formatters, lexers)

from gh_bugs import template


class Highlight(TestCase):
    def pyg_side_effect(*args, **kwargs):
        return namedtuple('Call', 'args kwargs')(args, kwargs)

    @patch('gh_bugs.template.pyg_highlight')
    @patch('sys.stdout')
    def test_no_highlight(self, stdout, pyg_highlight):
        stdout.isatty = Mock(return_value=False)
        pyg_highlight.side_effect = self.pyg_side_effect
        assert_equals(template.highlight('s'), 's')

    @patch('gh_bugs.template.pyg_highlight')
    @patch('sys.stdout')
    def test_highlight(self, stdout, pyg_highlight):
        stdout.isatty = Mock(return_value=True)
        pyg_highlight.side_effect = self.pyg_side_effect
        result = template.highlight('+++ a\n--- b\n+Test\n')
        assert_true(isinstance(result.args[2], lexers.DiffLexer))
        assert_true(isinstance(result.args[3],
                               formatters.terminal.TerminalFormatter))

    @patch('gh_bugs.template.pyg_highlight')
    @patch('sys.stdout')
    def test_highlight_lexer(self, stdout, pyg_highlight):
        stdout.isatty = Mock(return_value=True)
        pyg_highlight.side_effect = self.pyg_side_effect
        result = template.highlight('True', 'python')
        assert_true(isinstance(result.args[2], lexers.PythonLexer))

    @patch('gh_bugs.template.pyg_highlight')
    @patch('sys.stdout')
    def test_highlight_formatter(self, stdout, pyg_highlight):
        stdout.isatty = Mock(return_value=True)
        pyg_highlight.side_effect = self.pyg_side_effect
        result = template.highlight('True', formatter='terminal256')
        assert_true(isinstance(result.args[3],
                               formatters.terminal256.Terminal256Formatter))
