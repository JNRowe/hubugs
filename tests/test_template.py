#
# coding=utf-8
"""test_template - Test templating handling"""
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

from collections import namedtuple
from datetime import (datetime, timedelta)
from os import getenv
from unittest import TestCase

from expecter import expect
from mock import patch
from nose2.tools import params
from pygments import (formatters, lexers)

from hubugs import template

from tests.utils import (TerminalTypeError, unicode)


# We only test forced styling output of blessings, as blessings handles the
# sys.stdout.isatty() flipping
template.utils.T = template.utils.blessings.Terminal(force_styling=True)


class Colourise(TestCase):
    @params(
        ('red', unicode('\x1b[31'), unicode('\x1b[38;5;1m')),
        ('on blue', unicode('\x1b[44m'), unicode('\x1b[48;5;4m')),
        ('bold', unicode('\x1b[1m'), unicode('\x1b[1m')),
    )
    def test_color(self, attribute, linux_result, rxvt_result):
        if getenv('TERM') == 'linux':
            expect(template.colourise('s', attribute)).contains(linux_result)
        elif getenv('TERM').startswith('rxvt'):
            expect(template.colourise('s', attribute)).contains(rxvt_result)
        else:
            raise TerminalTypeError(getenv('TERM'))

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
    def getmtime_side_effect(file, response=list(range(100))):
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


class Markdown(TestCase):
    def test_basic(self):
        assert_equals(template.markdown('### hello'), '<h3>hello</h3>\n')


class Html2Text(TestCase):
    def test_basic(self):
        expect(template.html2text('<h3>hello</h3>')) == '### hello'

    def test_width(self):
        para = """<p>This is a long paragraph that needs wrapping to work so it
        doesn't make you want to claw your eyes out."""
        expect(template.html2text(para).count('\n')) == 1
        expect(template.html2text(para, width=20).count('\n')) == 5


@params(
    ({'days': 365, }, 'last year'),
    ({'days': 70, }, 'about two months ago'),
    ({'days': 30, }, 'last month'),
    ({'days': 21, }, 'about three weeks ago'),
    ({'days': 4, }, 'about four days ago'),
    ({'days': 1, }, 'yesterday'),
    ({'hours': 5, }, 'about five hours ago'),
    ({'hours': 1, }, 'about an hour ago'),
    ({'minutes': 6, }, 'about six minutes ago'),
    ({'seconds': 12, }, 'about 12 seconds ago'),
)
def test_relative_time(delta, result):
    dt = datetime.utcnow() - timedelta(**delta)
    expect(template.relative_time(dt)) == result


@params(
    ('edit', 'default.mkd'),
    ('view', 'issue.txt'),
)
def test_get_template(group, name):
    t = template.get_template(group, name)
    expect(t.filename.endswith('/templates/default/%s/%s' % (group, name))) \
        == True


@patch('hubugs.template.ENV')
def test_jinja_filter(env):
    env.filters = {}

    def null_func():
        pass

    template.jinja_filter(null_func)
    expect(template.ENV.filters['null_func']) == null_func
