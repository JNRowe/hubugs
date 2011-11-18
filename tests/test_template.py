from collections import namedtuple
from unittest import TestCase

from datetime import (datetime, timedelta)
from dateutil import tz
from mock import (Mock, patch)
from nose.tools import (assert_equals, assert_true, raises)
from pygments import (formatters, lexers)

from hubugs import template


class Colourise(TestCase):
    @patch('sys.stdout')
    def test_no_color(self, stdout):
        stdout.isatty = Mock(return_value=False)
        assert_equals(template.colourise('s', 'red'), 's')

    @patch('sys.stdout')
    def test_color(self, stdout):
        stdout.isatty = Mock(return_value=True)
        assert_equals(template.colourise('s', 'red'), '\x1b[31ms\x1b[0m')

    @patch('sys.stdout')
    def test_background_color(self, stdout):
        stdout.isatty = Mock(return_value=True)
        assert_equals(template.colourise('s', on_color='on_blue'),
                      '\x1b[44ms\x1b[0m')

    @patch('sys.stdout')
    def test_attribute(self, stdout):
        stdout.isatty = Mock(return_value=True)
        assert_equals(template.colourise('s', attrs=['bold', ]),
                      '\x1b[1ms\x1b[0m')

    @patch('sys.stdout')
    @raises(KeyError)
    def test_invalid_colour(self, stdout):
        stdout.isatty = Mock(return_value=True)
        assert_equals(template.colourise('s', 'mauve with a hint of green'), 's')


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

class Markdown(TestCase):
    def test_basic(self):
        assert_equals(template.markdown('### hello'), '<h3>hello</h3>\n')

    def test_smarty_pants(self):
        assert_equals(template.markdown('"hello"'),
                      '<p>&#8220;hello&#8221;</p>\n')


class Html2Text(TestCase):
    def test_basic(self):
        assert_equals(template.html2text('<h3>hello</h3>'), '### hello\n\n')

    def test_width(self):
        para = """<p>This is a long paragraph that needs wrapping to work so it
        doesn't make you want to claw your eyes out."""
        assert_equals(template.html2text(para).count('\n'), 3)
        assert_equals(template.html2text(para, width=20).count('\n'), 7)


class RelativeTime(TestCase):
    @staticmethod
    def now():
        return datetime.utcnow().replace(tzinfo=tz.tzutc())

    def test_last_year(self):
        dt = self.now() - timedelta(days=365)
        assert_equals(template.relative_time(dt), 'last year')

    def test_months_ago(self):
        dt = self.now() - timedelta(days=70)
        assert_equals(template.relative_time(dt), 'about two months ago')

    def test_month_ago(self):
        dt = self.now() - timedelta(days=30)
        assert_equals(template.relative_time(dt), 'last month')

    def test_weeks_ago(self):
        dt = self.now() - timedelta(days=21)
        assert_equals(template.relative_time(dt), 'about three weeks ago')

    def test_days_ago(self):
        dt = self.now() - timedelta(days=4)
        assert_equals(template.relative_time(dt), 'about four days ago')

    def test_yesterday(self):
        dt = self.now() - timedelta(days=1)
        assert_equals(template.relative_time(dt), 'yesterday')

    def test_hours_ago(self):
        dt = self.now() - timedelta(hours=5)
        assert_equals(template.relative_time(dt), 'about five hours ago')

    def test_hour_ago(self):
        dt = self.now() - timedelta(hours=1)
        assert_equals(template.relative_time(dt), 'about an hour ago')

    def test_minutes_ago(self):
        dt = self.now() - timedelta(minutes=6)
        assert_equals(template.relative_time(dt), 'about six minutes ago')

    def test_seconds_ago(self):
        dt = self.now() - timedelta(seconds=12)
        assert_equals(template.relative_time(dt), 'about 12 seconds ago')


class TermMarkdown(TestCase):
    @patch('sys.stdout')
    def test_no_formatting(self, stdout):
        stdout.isatty = Mock(return_value=False)
        assert_equals(template.term_markdown('### hello'), '### hello')

    @patch('sys.stdout')
    def test_rule(self, stdout):
        stdout.isatty = Mock(return_value=True)
        assert_equals(template.term_markdown('- - -'), '\x1b[32m- - -\x1b[0m')
        assert_equals(template.term_markdown('- - - - -'),
                      '\x1b[32m- - - - -\x1b[0m')

    @patch('sys.stdout')
    def test_emphasis(self, stdout):
        stdout.isatty = Mock(return_value=True)
        assert_equals(template.term_markdown('this is *emphasis*'),
                      'this is \x1b[1memphasis\x1b[0m')
        assert_equals(template.term_markdown('this is _emphasis_'),
                      'this is \x1b[1memphasis\x1b[0m')

    @patch('sys.stdout')
    def test_strong_emphasis(self, stdout):
        stdout.isatty = Mock(return_value=True)
        assert_equals(template.term_markdown('this is **strong** emphasis'),
                      'this is \x1b[4mstrong\x1b[0m emphasis')
        assert_equals(template.term_markdown('this is __strong__ emphasis'),
                      'this is \x1b[4mstrong\x1b[0m emphasis')


    @patch('sys.stdout')
    def test_fancy_bullet(self, stdout):
        stdout.isatty = Mock(return_value=True)
        stdout.encoding = 'UTF-8'
        assert_equals(template.term_markdown('* list item'),
                      u'\u2022 list item')
        assert_equals(template.term_markdown('+ list item'),
                      u'\u2022 list item')
        assert_equals(template.term_markdown('- list item'),
                      u'\u2022 list item')
