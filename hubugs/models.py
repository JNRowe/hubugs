#
# coding=utf-8
"""models - GitHub models for hubugs"""
# Copyright (C) 2010-2012  James Rowe <jnrowe@gmail.com>
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

import micromodels


class ISODateTimeField(micromodels.DateTimeField):
    def __init__(self, **kwargs):
        super(ISODateTimeField, self).__init__(format='%Y-%m-%dT%H:%M:%SZ',
                                               **kwargs)


class Application(micromodels.Model):
    url = micromodels.CharField()
    name = micromodels.CharField()

    def __repr__(self):
        return "<%s %r>" % (self.__class__.__name__, self.name)


class Authorisation(micromodels.Model):
    id = micromodels.IntegerField()
    url = micromodels.CharField()
    scopes = micromodels.FieldCollectionField(micromodels.CharField())
    token = micromodels.CharField()
    app = micromodels.ModelField(Application)
    note = micromodels.CharField()
    note_url = micromodels.CharField()
    created_at = ISODateTimeField()
    updated_at = ISODateTimeField()

    def __repr__(self):
        return "<%s %s %r>" % (self.__class__.__name__, self.id,
                               self.note[:20])
