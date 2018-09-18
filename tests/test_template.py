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

from html2text import __version__ as h2t_version
from mock import patch
from pygments import (formatters, lexers)
from pytest import mark, raises

from hubugs import template


@mark.parametrize('fg, bg, attributes, expected', [
    ('red', None, {}, '\x1b[31'),
    (None, 'blue', {}, '\x1b[44m'),
    (None, None, {'bold': True}, '\x1b[1m'),
])
def test_Colourise_color(fg, bg, attributes, expected):
    output = template.colourise('s', fg, bg, **attributes)
    assert expected in output


def test_Colourise_invalid_colour():
    with raises(TypeError):
        template.colourise('s', 'mauve with a hint of green')


def pyg_side_effect(*args, **kwargs):
    return namedtuple('Call', 'args kwargs')(args, kwargs)


def test_highlight():
    with patch('hubugs.template.pyg_highlight') as pyg_highlight, \
         patch('sys.stdout.isatty') as isatty:
        pyg_highlight.side_effect = pyg_side_effect
        isatty.side_effect = lambda: True

        result = template.highlight('+++ a\n--- b\n+Test\n')
        assert isinstance(result.args[1], lexers.DiffLexer)
        assert isinstance(result.args[2],
                          formatters.terminal.TerminalFormatter)


def test_highlight_lexer():
    with patch('hubugs.template.pyg_highlight') as pyg_highlight, \
         patch('sys.stdout.isatty') as isatty:
        pyg_highlight.side_effect = pyg_side_effect
        isatty.side_effect = lambda: True

        result = template.highlight('True', 'python')
        assert isinstance(result.args[1], lexers.PythonLexer)


def test_highlight_formatter():
    with patch('hubugs.template.pyg_highlight') as pyg_highlight, \
         patch('sys.stdout.isatty') as isatty:
        pyg_highlight.side_effect = pyg_side_effect
        isatty.side_effect = lambda: True

        result = template.highlight('True', formatter='terminal256')
        assert isinstance(result.args[2],
                          formatters.terminal256.Terminal256Formatter)


def test_EditText_no_message():
    with patch('click.edit') as edit:
        edit.return_value = None

        with raises(template.EmptyMessageError):
            template.edit_text()


def test_EditText_message():
    with patch('click.edit') as edit:
        edit.return_value = 'Some message'

        assert template.edit_text() == 'Some message'


def test_EditText_message_prefill():
    with patch('click.edit') as edit:
        edit.side_effect = lambda t, *args, **kwargs: t

        data = {'title': 'Some message'}
        assert template.edit_text('open', data) == data['title']


def test_Markdown_basic():
    assert template.markdown('### hello') == '<h3>hello</h3>\n'


def test_Html2Text_basic():
    assert template.html2text('<h3>hello</h3>') == '### hello'


def test_Html2Text_width():
    para = """<p>This is a long paragraph that needs wrapping to work so it
    doesn’t make you want to claw your eyes out."""
    assert template.html2text(para).count('\n') == 1
    # FIXME: Recent html2text version have changed API
    if isinstance(h2t_version, str) and h2t_version <= '2014.4.5':
        assert template.html2text(para, width=20).count('\n') == 1


@mark.parametrize('delta, result', [
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
])
def test_relative_time(delta, result):
    dt = datetime.utcnow() - timedelta(**delta)
    assert template.relative_time(dt) == result


@mark.parametrize('group, name', [
    ('edit', 'default.mkd'),
    ('view', 'issue.txt'),
])
def test_get_template(group, name):
    t = template.get_template(group, name)
    assert t.filename.endswith('/templates/default/%s/%s' % (group, name))


def test_jinja_filter():
    with patch('hubugs.template.ENV') as env:
        env.filters = {}

        def null_func():
            pass

        template.jinja_filter(null_func)
        assert template.ENV.filters['null_func'] == null_func
