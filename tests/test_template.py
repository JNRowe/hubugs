#
"""test_template - Test templating handling."""
# Copyright © 2011-2018  James Rowe <jnrowe@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0+
#
# This file is part of hubugs.
#
# hubugs is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# hubugs is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# hubugs.  If not, see <http://www.gnu.org/licenses/>.

from collections import namedtuple
from datetime import (datetime, timedelta)
from typing import Dict, Optional

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
def test_Colourise_color(fg: str, bg: Optional[str],
                         attributes: Dict[str, bool], expected: str):
    output = template.colourise('s', fg, bg, **attributes)
    assert expected in output


def test_Colourise_invalid_colour():
    with raises(TypeError):
        template.colourise('s', 'mauve with a hint of green')


def pyg_side_effect(*args, **kwargs):
    return namedtuple('Call', 'args kwargs')(args, kwargs)


def test_highlight(monkeypatch):
    monkeypatch.setattr('hubugs.template.pyg_highlight', pyg_side_effect)
    monkeypatch.setattr('sys.stdout.isatty', lambda: True)

    result = template.highlight('+++ a\n--- b\n+Test\n')
    assert isinstance(result.args[1], lexers.DiffLexer)
    assert isinstance(result.args[2], formatters.terminal.TerminalFormatter)


def test_highlight_lexer(monkeypatch):
    monkeypatch.setattr('hubugs.template.pyg_highlight', pyg_side_effect)
    monkeypatch.setattr('sys.stdout.isatty', lambda: True)

    result = template.highlight('True', 'python')
    assert isinstance(result.args[1], lexers.PythonLexer)


def test_highlight_formatter(monkeypatch):
    monkeypatch.setattr('hubugs.template.pyg_highlight', pyg_side_effect)
    monkeypatch.setattr('sys.stdout.isatty', lambda: True)

    result = template.highlight('True', formatter='terminal256')
    assert isinstance(result.args[2],
                      formatters.terminal256.Terminal256Formatter)


def test_EditText_no_message(monkeypatch):
    monkeypatch.setattr('click.edit', lambda *args, **kwargs: None)

    with raises(template.EmptyMessageError):
        template.edit_text()


def test_EditText_message(monkeypatch):
    monkeypatch.setattr('click.edit', lambda *args, **kwargs: 'Some message')

    assert template.edit_text() == 'Some message'


def test_EditText_message_prefill(monkeypatch):
    monkeypatch.setattr('click.edit', lambda t, *args, **kwargs: t)

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


@mark.parametrize('group, name', [
    ('edit', 'default.mkd'),
    ('view', 'issue.txt'),
])
def test_get_template(group: str, name: str):
    t = template.get_template(group, name)
    assert t.filename.endswith('/templates/default/%s/%s' % (group, name))


def test_jinja_filter(monkeypatch):
    monkeypatch.setattr('hubugs.template.ENV.filters', {})

    def null_func():
        pass

    template.jinja_filter(null_func)
    assert template.ENV.filters['null_func'] == null_func
