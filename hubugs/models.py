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

import datetime

from schematics.models import Model
from schematics.types import (BooleanType, DateTimeType, IntType, StringType,
                              URLType)
from schematics.types.compound import (ListType, ModelType, SortedListType)


class ValidatingModel(Model):
    def __init__(self, *args, **kwargs):
        super(ValidatingModel, self).__init__(*args, **kwargs)
        self.validate()


class User(ValidatingModel):

    """GitHub user model."""

    id = IntType()
    avatar_url = URLType()
    gravatar_id = StringType()
    login = StringType()
    url = URLType(required=True)

    def __repr__(self):
        return "<%s %r>" % (self.__class__.__name__, self.login)


class Label(ValidatingModel):

    """GitHub issue label model."""

    color = StringType(regex='[0-9a-f]{6}')
    name = StringType()
    url = URLType(required=True)

    def __repr__(self):
        return "<%s %r>" % (self.__class__.__name__, self.name)


class PullRequest(ValidatingModel):

    """GitHub issue pull request data model."""

    diff_url = URLType()
    html_url = URLType()
    patch_url = URLType()

    def __nonzero__(self):
        return bool(self.patch_url)

    def __repr__(self):
        return "<%s %r>" % (self.__class__.__name__, self.patch_url)


class Issue(ValidatingModel):

    """GitHub issue model."""

    id = IntType()
    assignee = ModelType(User)
    body = StringType()
    body_html = StringType()
    closed_at = DateTimeType()
    closed_by = ModelType(User)
    comments = IntType()
    created_at = DateTimeType()
    html_url = URLType()
    labels = SortedListType(ModelType(Label))
    milestone = StringType()
    number = IntType()
    pull_request = ModelType(PullRequest)
    state = StringType(choices=['open', 'closed'])
    title = StringType()
    updated_at = DateTimeType()
    url = URLType(required=True)
    user = ModelType(User)

    def __repr__(self):
        return "<%s %s %r>" % (self.__class__.__name__, self.id,
                               self.title[:20])

    @classmethod
    def from_search(cls, d):
        """Support legacy API search results as API v3 issues(-ish)

        This is an awful hack to workaround the lack of search support in API
        v3.  It needs to be removed at the first possible opportunity.

        """

        avatar_url = ("https://secure.gravatar.com/avatar/%s?d="
                      "https://a248.e.akamai.net/assets.github.com%%2F"
                      "images%%2Fgravatars%%2Fgravatar-140.png")
        label_url = 'https://api.github.com/repos/%s/%s/labels/%s'

        owner, project = d['html_url'].split('/')[3:5]

        d['id'] = '<from search>'
        d['user'] = {
            'avatar_url': avatar_url % d['gravatar_id'],
            'gravatar_id': d['gravatar_id'],
            'login': d['user'],
            'url': 'https://api.github.com/users/%s' % d['user'],
        }
        if 'closed_by' in d:
            d['closed_by'] = {
                'avatar_url': avatar_url % d['closed_by'],
                'gravatar_id': d['gravatar_id'],
                'login': d['user'],
                'url': 'https://api.github.com/users/%s' % d['user'],
            }
            d['closed_at'] = cls._v2_conv_timestamp(d['closed_at'])
        d['created_at'] = cls._v2_conv_timestamp(d['created_at'])
        d['updated_at'] = cls._v2_conv_timestamp(d['updated_at'])
        if d['labels']:
            labels = []
            for name in d['labels']:
                labels.append({
                    'color': '000000',
                    'name': name,
                    'url': label_url % (owner, project, name)
                })
            d['labels'] = labels
        return cls(**d)

    @staticmethod
    def _v2_conv_timestamp(s):
        zone = datetime.timedelta(hours=int(s[-5:-3]))
        stamp = datetime.datetime.strptime(s[:-6], '%Y-%m-%dT%H:%M:%S')
        return (stamp - zone).isoformat() + 'Z'


class Comment(ValidatingModel):

    """GitHub issue comment model."""

    id = IntType()
    body = StringType()
    body_html = StringType()
    created_at = DateTimeType()
    updated_at = DateTimeType()
    url = URLType(required=True)
    user = ModelType(User)

    def __repr__(self):
        return "<%s %s %r>" % (self.__class__.__name__, self.id,
                               self.body[:20])


class Application(ValidatingModel):

    """GitHub OAuth application model."""

    name = StringType()
    url = URLType(required=True)

    def __repr__(self):
        return "<%s %r>" % (self.__class__.__name__, self.name)


class Authorisation(ValidatingModel):

    """GitHub OAuth authorisation model."""

    id = IntType()
    app = ModelType(Application)
    created_at = DateTimeType()
    note = StringType(default='')
    note_url = URLType()
    scopes = ListType(StringType())
    token = StringType()
    updated_at = DateTimeType()
    url = URLType(required=True)

    def __repr__(self):
        return "<%s %s %r>" % (self.__class__.__name__, self.id,
                               self.note[:20])


class Organization(ValidatingModel):

    """GitHub issue organisation model."""

    id = IntType()
    avatar_url = URLType()
    gravatar_id = StringType()
    login = StringType()
    type = StringType()
    url = URLType(required=True)


class Repository(ValidatingModel):

    """GitHub repository model."""

    id = IntType()
    clone_url = URLType()
    created_at = DateTimeType()
    description = StringType()
    fork = BooleanType()
    forks = IntType()
    git_url = StringType(regex=r'git://github.com/[^/]+/[^/]+.git$')
    has_downloads = BooleanType()
    has_issues = BooleanType()
    has_wiki = BooleanType()
    homepage = StringType()
    html_url = URLType()
    language = StringType()
    master_branch = StringType()
    mirror_url = URLType()
    name = StringType()
    open_issues = IntType()
    owner = ModelType(User)
    private = BooleanType()
    pushed_at = DateTimeType()
    size = IntType()
    url = URLType(required=True)
    watchers = IntType()
