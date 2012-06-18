from collections import namedtuple
from unittest import TestCase

from datetime import (datetime, timedelta)
from expecter import expect
from mock import patch
from pygments import (formatters, lexers)

from hubugs import template

from utils import skip_check


# We only test forced styling output of blessings, as blessings handles the
# sys.stdout.isatty() flipping
template.utils.T = template.utils.blessings.Terminal(force_styling=True)


class Colourise(TestCase):
    @skip_check
    def test_color(self):
        expect(template.colourise('s', 'red')) == u'\x1b[38;5;1ms\x1b[m\x1b(B'

    @skip_check
    def test_background_color(self):
        expect(template.colourise('s', 'on blue')) \
            == u'\x1b[48;5;4ms\x1b[m\x1b(B'

    @skip_check
    def test_attribute(self):
        expect(template.colourise('s', 'bold')) == u'\x1b[1ms\x1b[m\x1b(B'

    @skip_check
    def test_invalid_colour(self):
        with expect.raises(TypeError):
            template.colourise('s', 'mauve with a hint of green')


class Highlight(TestCase):
    def pyg_side_effect(*args, **kwargs):
        return namedtuple('Call', 'args kwargs')(args, kwargs)

    @patch('hubugs.template.pyg_highlight')
    def test_highlight(self, pyg_highlight):
        pyg_highlight.side_effect = self.pyg_side_effect
        result = template.highlight('+++ a\n--- b\n+Test\n')
        expect(isinstance(result.args[2], lexers.DiffLexer)) == True
        expect(isinstance(result.args[3],
                          formatters.terminal.TerminalFormatter)) == True

    @patch('hubugs.template.pyg_highlight')
    def test_highlight_lexer(self, pyg_highlight):
        pyg_highlight.side_effect = self.pyg_side_effect
        result = template.highlight('True', 'python')
        expect(isinstance(result.args[2], lexers.PythonLexer)) == True

    @patch('hubugs.template.pyg_highlight')
    def test_highlight_formatter(self, pyg_highlight):
        pyg_highlight.side_effect = self.pyg_side_effect
        result = template.highlight('True', formatter='terminal256')
        expect(isinstance(result.args[3],
                          formatters.terminal256.Terminal256Formatter)) \
            == True


class EditText(TestCase):
    @staticmethod
    def getmtime_side_effect(file, response=range(100)):
        return response.pop()

    @staticmethod
    def check_call_side_effect(args):
        open(args[1], 'a').write('Some message')

    @patch('subprocess.check_call')
    def test_no_message(self, check_call):
        check_call.return_value = True
        with expect.raises(template.EmptyMessageError):
            template.edit_text()

    @patch('subprocess.check_call')
    @patch('os.path.getmtime')
    def test_message(self, getmtime, check_call):
        getmtime.side_effect = self.getmtime_side_effect
        check_call.side_effect = self.check_call_side_effect

        expect(template.edit_text()) == 'Some message'

    @patch('subprocess.check_call')
    @patch('os.path.getmtime')
    def test_message_comments(self, getmtime, check_call):
        getmtime.side_effect = self.getmtime_side_effect
        check_call.side_effect = self.check_call_side_effect

        expect(template.edit_text()) == 'Some message'

    @patch('subprocess.check_call')
    def test_message_prefill(self, check_call):
        check_call.return_value = True
        with expect.raises(template.EmptyMessageError):
            template.edit_text('open', data={'title': 'Some message'})


class Html2Text(TestCase):
    def test_basic(self):
        expect(template.html2text('<h3>hello</h3>')) == '### hello'

    def test_width(self):
        para = """<p>This is a long paragraph that needs wrapping to work so it
        doesn't make you want to claw your eyes out."""
        expect(template.html2text(para).count('\n')) == 1
        expect(template.html2text(para, width=20).count('\n')) == 5


class RelativeTime(TestCase):
    def test_last_year(self):
        dt = datetime.utcnow() - timedelta(days=365)
        expect(template.relative_time(dt)) == 'last year'

    def test_months_ago(self):
        dt = datetime.utcnow() - timedelta(days=70)
        expect(template.relative_time(dt)) == 'about two months ago'

    def test_month_ago(self):
        dt = datetime.utcnow() - timedelta(days=30)
        expect(template.relative_time(dt)) == 'last month'

    def test_weeks_ago(self):
        dt = datetime.utcnow() - timedelta(days=21)
        expect(template.relative_time(dt)) == 'about three weeks ago'

    def test_days_ago(self):
        dt = datetime.utcnow() - timedelta(days=4)
        expect(template.relative_time(dt)) == 'about four days ago'

    def test_yesterday(self):
        dt = datetime.utcnow() - timedelta(days=1)
        expect(template.relative_time(dt)) == 'yesterday'

    def test_hours_ago(self):
        dt = datetime.utcnow() - timedelta(hours=5)
        expect(template.relative_time(dt)) == 'about five hours ago'

    def test_hour_ago(self):
        dt = datetime.utcnow() - timedelta(hours=1)
        expect(template.relative_time(dt)) == 'about an hour ago'

    def test_minutes_ago(self):
        dt = datetime.utcnow() - timedelta(minutes=6)
        expect(template.relative_time(dt)) == 'about six minutes ago'

    def test_seconds_ago(self):
        dt = datetime.utcnow() - timedelta(seconds=12)
        expect(template.relative_time(dt)) == 'about 12 seconds ago'
