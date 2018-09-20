#
"""test_attrdict - Test AttrDict support"""
# Copyright © 2010, 2011, 2012, 2013, 2014  James Rowe <jnrowe@gmail.com>
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

from hubugs.utils import AttrDict


class TestAttrDict:
    def setup_method(self, method):
        self.ad = AttrDict(carrots=3, snacks=0)

    def test_base(self):
        assert isinstance(self.ad, dict)

        assert self.ad['carrots'] == 3
        assert self.ad['snacks'] == 0

        assert sorted(self.ad.keys()) == ['carrots', 'snacks']

    def test___contains__(self):
        assert 'carrots' in self.ad
        assert 'prizes' not in self.ad

    def test___getattr__(self):
        assert self.ad.carrots == 3
        assert self.ad.snacks == 0

    def test___setattr__(self):
        self.ad.carrots, self.ad.snacks = 0, 3
        assert self.ad.carrots == 0
        assert self.ad.snacks == 3

    def test___delattr__(self):
        assert 'carrots' in self.ad
        del self.ad['carrots']
        assert 'carrots' not in self.ad
