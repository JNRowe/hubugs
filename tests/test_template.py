from collections import namedtuple
from unittest import TestCase

from datetime import (datetime, timedelta)
from dateutil import tz
from mock import patch
from nose.tools import (assert_equals, assert_true, raises)
from pygments import (formatters, lexers)

from hubugs import template


# We only test forced styling output of blessings, as blessings handles the
# sys.stdout.isatty() flipping
template.utils.T = template.utils.blessings.Terminal(force_styling=True)


class Colourise(TestCase):
    def test_color(self):
        assert_equals(template.colourise('s', 'red'),
                      u'\x1b[38;5;1ms\x1b[m\x1b(B')

    def test_background_color(self):
        assert_equals(template.colourise('s', 'on blue'),
                                         u'\x1b[48;5;4ms\x1b[m\x1b(B')

    def test_attribute(self):
        assert_equals(template.colourise('s', 'bold'), u'\x1b[1ms\x1b[m\x1b(B')

    @raises(TypeError)
    def test_invalid_colour(self):
        assert_equals(template.colourise('s', 'mauve with a hint of green'),
                                         's')


class Highlight(TestCase):
    def pyg_side_effect(*args, **kwargs):
        return namedtuple('Call', 'args kwargs')(args, kwargs)

    @patch('hubugs.template.pyg_highlight')
    def test_highlight(self, pyg_highlight):
        pyg_highlight.side_effect = self.pyg_side_effect
        result = template.highlight('+++ a\n--- b\n+Test\n')
        assert_true(isinstance(result.args[2], lexers.DiffLexer))
        assert_true(isinstance(result.args[3],
                               formatters.terminal.TerminalFormatter))

    @patch('hubugs.template.pyg_highlight')
    def test_highlight_lexer(self, pyg_highlight):
        pyg_highlight.side_effect = self.pyg_side_effect
        result = template.highlight('True', 'python')
        assert_true(isinstance(result.args[2], lexers.PythonLexer))

    @patch('hubugs.template.pyg_highlight')
    def test_highlight_formatter(self, pyg_highlight):
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


class Html2Text(TestCase):
    def test_basic(self):
        assert_equals(template.html2text('<h3>hello</h3>'), '### hello')

    def test_width(self):
        para = """<p>This is a long paragraph that needs wrapping to work so it
        doesn't make you want to claw your eyes out."""
        assert_equals(template.html2text(para).count('\n'), 1)
        assert_equals(template.html2text(para, width=20).count('\n'), 5)


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
    def test_rule(self, stdout):
        stdout.encoding = 'UTF-8'
        assert_equals(template.term_markdown('- - -'),
                      u'\x1b[38;5;2m- - -\x1b[m\x1b(B')
        assert_equals(template.term_markdown('- - - - -'),
                      u'\x1b[38;5;2m- - - - -\x1b[m\x1b(B')

    @patch('sys.stdout')
    def test_emphasis(self, stdout):
        stdout.encoding = 'UTF-8'
        assert_equals(template.term_markdown('this is *emphasis*'),
                      u'this is \x1b[1memphasis\x1b[m\x1b(B')
        assert_equals(template.term_markdown('this is _emphasis_'),
                      u'this is \x1b[1memphasis\x1b[m\x1b(B')

    @patch('sys.stdout')
    def test_strong_emphasis(self, stdout):
        stdout.encoding = 'UTF-8'
        assert_equals(template.term_markdown('this is **strong** emphasis'),
                      u'this is \x1b[4mstrong\x1b[m\x1b(B emphasis')
        assert_equals(template.term_markdown('this is __strong__ emphasis'),
                      u'this is \x1b[4mstrong\x1b[m\x1b(B emphasis')

    @patch('sys.stdout')
    def test_fancy_bullet(self, stdout):
        stdout.encoding = 'UTF-8'
        assert_equals(template.term_markdown('* list item'),
                      u'\u2022 list item')
        assert_equals(template.term_markdown('+ list item'),
                      u'\u2022 list item')
        assert_equals(template.term_markdown('- list item'),
                      u'\u2022 list item')
