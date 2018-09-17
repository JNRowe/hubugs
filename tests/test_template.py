#
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
from unittest import TestCase

from html2text import __version__ as h2t_version
from mock import patch
from nose2.tools import params
from pygments import (formatters, lexers)
from pytest import raises

from hubugs import template


class Colourise(TestCase):
    @params(
        ('red', None, {}, '\x1b[31'),
        (None, 'blue', {}, '\x1b[44m'),
        (None, None, {'bold': True}, '\x1b[1m'),
    )
    def test_color(self, fg, bg, attributes, expected):
        output = template.colourise('s', fg, bg, **attributes)
        assert expected in output

    def test_invalid_colour(self):
        with raises(TypeError):
            template.colourise('s', 'mauve with a hint of green')


class Highlight(TestCase):
    def pyg_side_effect(*args, **kwargs):
        return namedtuple('Call', 'args kwargs')(args, kwargs)

    @patch('hubugs.template.pyg_highlight')
    def test_highlight(self, pyg_highlight):
        pyg_highlight.side_effect = self.pyg_side_effect
        result = template.highlight('+++ a\n--- b\n+Test\n')
        assert isinstance(result.args[2], lexers.DiffLexer)
        assert isinstance(result.args[3],
                          formatters.terminal.TerminalFormatter)

    @patch('hubugs.template.pyg_highlight')
    def test_highlight_lexer(self, pyg_highlight):
        pyg_highlight.side_effect = self.pyg_side_effect
        result = template.highlight('True', 'python')
        assert isinstance(result.args[2], lexers.PythonLexer)

    @patch('hubugs.template.pyg_highlight')
    def test_highlight_formatter(self, pyg_highlight):
        pyg_highlight.side_effect = self.pyg_side_effect
        result = template.highlight('True', formatter='terminal256')
        assert isinstance(result.args[3],
                          formatters.terminal256.Terminal256Formatter)


class EditText(TestCase):
    @patch('click.edit')
    def test_no_message(self, edit):
        edit.return_value = None
        with raises(template.EmptyMessageError):
            template.edit_text()

    @patch('click.edit')
    def test_message(self, edit):
        edit.return_value = 'Some message'
        assert template.edit_text() == 'Some message'

    @patch('click.edit')
    def test_message_prefill(self, edit):
        edit.side_effect = lambda t, *args, **kwargs: t
        data = {'title': 'Some message'}
        assert template.edit_text('open', data) == data['title']


class Markdown(TestCase):
    def test_basic(self):
        assert template.markdown('### hello') == '<h3>hello</h3>\n'


class Html2Text(TestCase):
    def test_basic(self):
        assert template.html2text('<h3>hello</h3>') == '### hello'

    def test_width(self):
        para = """<p>This is a long paragraph that needs wrapping to work so it
        doesn’t make you want to claw your eyes out."""
        assert template.html2text(para).count('\n') == 1
        # FIXME: Recent html2text version have changed API
        if isinstance(h2t_version, str) and h2t_version <= '2014.4.5':
            assert template.html2text(para, width=20).count('\n') == 1


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
    assert template.relative_time(dt) == result


@params(
    ('edit', 'default.mkd'),
    ('view', 'issue.txt'),
)
def test_get_template(group, name):
    t = template.get_template(group, name)
    assert t.filename.endswith('/templates/default/%s/%s' % (group, name))


@patch('hubugs.template.ENV')
def test_jinja_filter(env):
    env.filters = {}

    def null_func():
        pass

    template.jinja_filter(null_func)
    assert template.ENV.filters['null_func'] == null_func
