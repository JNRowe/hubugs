from collections import namedtuple
from unittest import TestCase

from mock import (Mock, patch)
from nose.tools import (assert_equals, assert_true, raises)
from pygments import (formatters, lexers)

from hubugs import template


class Highlight(TestCase):
    def pyg_side_effect(*args, **kwargs):
        return namedtuple('Call', 'args kwargs')(args, kwargs)

    @patch('hubugs.template.pyg_highlight')
    @patch('sys.stdout')
    def test_no_highlight(self, stdout, pyg_highlight):
        stdout.isatty = Mock(return_value=False)
        pyg_highlight.side_effect = self.pyg_side_effect
        assert_equals(template.highlight('s'), 's')

    @patch('hubugs.template.pyg_highlight')
    @patch('sys.stdout')
    def test_highlight(self, stdout, pyg_highlight):
        stdout.isatty = Mock(return_value=True)
        pyg_highlight.side_effect = self.pyg_side_effect
        result = template.highlight('+++ a\n--- b\n+Test\n')
        assert_true(isinstance(result.args[2], lexers.DiffLexer))
        assert_true(isinstance(result.args[3],
                               formatters.terminal.TerminalFormatter))

    @patch('hubugs.template.pyg_highlight')
    @patch('sys.stdout')
    def test_highlight_lexer(self, stdout, pyg_highlight):
        stdout.isatty = Mock(return_value=True)
        pyg_highlight.side_effect = self.pyg_side_effect
        result = template.highlight('True', 'python')
        assert_true(isinstance(result.args[2], lexers.PythonLexer))

    @patch('hubugs.template.pyg_highlight')
    @patch('sys.stdout')
    def test_highlight_formatter(self, stdout, pyg_highlight):
        stdout.isatty = Mock(return_value=True)
        pyg_highlight.side_effect = self.pyg_side_effect
        result = template.highlight('True', formatter='terminal256')
        assert_true(isinstance(result.args[3],
                               formatters.terminal256.Terminal256Formatter))


class EditText(TestCase):
    @patch('subprocess.check_call')
    @raises(template.EmptyMessageError)
    def test_no_message(self, check_call):
        check_call.return_value = True
        template.edit_text()

    @patch('subprocess.check_call')
    def test_message(self, check_call):
        def side_effect(args):
            open(args[1], 'w').write('Some message')
        check_call.side_effect = side_effect
        assert_equals(template.edit_text(), 'Some message')

    @patch('subprocess.check_call')
    def test_message_comments(self, check_call):
        def side_effect(args):
            open(args[1], 'w').write('Some message\n#Some comment')
        check_call.side_effect = side_effect
        assert_equals(template.edit_text(), 'Some message')

    @patch('subprocess.check_call')
    def test_message_prefill(self, check_call):
        check_call.return_value = True
        assert_equals(template.edit_text('open',
                                         data={'title': 'Some message'}),
                      'Some message')
