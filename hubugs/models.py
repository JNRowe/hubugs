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

import micromodels


class ISODateTimeField(micromodels.DateTimeField):

    """ISO-8601 compliant date and time field."""

    def __init__(self, **kwargs):
        super(ISODateTimeField, self).__init__(format='%Y-%m-%dT%H:%M:%SZ',
                                               **kwargs)


class User(micromodels.Model):

    """GitHub user model."""

    id = micromodels.IntegerField()
    avatar_url = micromodels.CharField()
    gravatar_id = micromodels.CharField()
    login = micromodels.CharField()
    url = micromodels.CharField()

    def __repr__(self):
        return "<%s %r>" % (self.__class__.__name__, self.login)


class Label(micromodels.Model):

    """GitHub issue label model."""

    color = micromodels.CharField()
    name = micromodels.CharField()
    url = micromodels.CharField()

    def __repr__(self):
        return "<%s %r>" % (self.__class__.__name__, self.name)


class PullRequest(micromodels.Model):

    """GitHub issue pull request data model."""

    diff_url = micromodels.CharField()
    html_url = micromodels.CharField()
    patch_url = micromodels.CharField()

    def __nonzero__(self):
        return bool(self.patch_url)

    def __repr__(self):
        return "<%s %r>" % (self.__class__.__name__, self.patch_url)


class Issue(micromodels.Model):

    """GitHub issue model."""

    id = micromodels.IntegerField()
    assignee = micromodels.ModelField(User)
    body = micromodels.CharField()
    body_html = micromodels.CharField()
    closed_at = ISODateTimeField()
    closed_by = micromodels.ModelField(User)
    comments = micromodels.IntegerField()
    created_at = ISODateTimeField()
    html_url = micromodels.CharField()
    labels = micromodels.ModelCollectionField(Label)
    milestone = micromodels.CharField()
    number = micromodels.IntegerField()
    pull_request = micromodels.ModelField(PullRequest)
    state = micromodels.CharField()
    title = micromodels.CharField()
    updated_at = ISODateTimeField()
    url = micromodels.CharField()
    user = micromodels.ModelField(User)

    def __repr__(self):
        return "<%s %s %r>" % (self.__class__.__name__, self.id,
                               self.title[:20])

    @classmethod
    def from_search(cls, d):
        """Support legacy API search results as API v3 issues(-ish)

        This is an awful hack to workaround the lack of search support in API
        v3.  It needs to be removed at the first possible opportunity.

        """

        d['id'] = '<from search>'
        d['user'] = {
            'avatar_url': "https://secure.gravatar.com/avatar/%s?d=https://a248.e.akamai.net/assets.github.com%%2Fimages%%2Fgravatars%%2Fgravatar-140.png" % d['gravatar_id'],
            'gravatar_id': d['gravatar_id'],
            'login': d['user'],
            'url': 'https://api.github.com/users/%s' % d['user'],
        }
        if 'closed_by' in d:
            d['closed_by'] = {
                'avatar_url': "https://secure.gravatar.com/avatar/%s?d=https://a248.e.akamai.net/assets.github.com%%2Fimages%%2Fgravatars%%2Fgravatar-140.png" % d['closed_by'],
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
                    'url': 'https://api.github.com/repos/%s/%s/labels/%s' % tuple(d['html_url'].split('/')[3:5] + [name, ])
                })
            d['labels'] = labels
        return cls.from_dict(d)

    @staticmethod
    def _v2_conv_timestamp(s):
        zone = datetime.timedelta(hours=int(s[-5:-2]))
        stamp = datetime.datetime.strptime(s[:-6], '%Y/%m/%d %H:%M:%S')
        return (stamp - zone).isoformat() + 'Z'


class Comment(micromodels.Model):

    """GitHub issue comment model."""

    id = micromodels.IntegerField()
    body = micromodels.CharField()
    body_html = micromodels.CharField()
    created_at = ISODateTimeField()
    updated_at = ISODateTimeField()
    url = micromodels.CharField()
    user = micromodels.ModelField(User)

    def __repr__(self):
        return "<%s %s %r>" % (self.__class__.__name__, self.id,
                               self.body[:20])


class Application(micromodels.Model):

    """GitHub OAuth application model."""

    name = micromodels.CharField()
    url = micromodels.CharField()

    def __repr__(self):
        return "<%s %r>" % (self.__class__.__name__, self.name)


class Authorisation(micromodels.Model):

    """GitHub OAuth authorisation model."""

    id = micromodels.IntegerField()
    app = micromodels.ModelField(Application)
    created_at = ISODateTimeField()
    note = micromodels.CharField()
    note_url = micromodels.CharField()
    scopes = micromodels.FieldCollectionField(micromodels.CharField())
    token = micromodels.CharField()
    updated_at = ISODateTimeField()
    url = micromodels.CharField()

    def __repr__(self):
        return "<%s %s %r>" % (self.__class__.__name__, self.id,
                               self.note[:20])


class Organization(micromodels.Model):

    """GitHub issue organisation model."""

    id = micromodels.IntegerField()
    avatar_url = micromodels.CharField()
    gravatar_id = micromodels.CharField()
    login = micromodels.CharField()
    type = micromodels.CharField()
    url = micromodels.CharField()


class Repository(micromodels.Model):

    """GitHub repository model."""

    id = micromodels.IntegerField()
    clone_url = micromodels.CharField()
    created_at = ISODateTimeField()
    description = micromodels.CharField()
    fork = micromodels.BooleanField()
    forks = micromodels.IntegerField()
    git_url = micromodels.CharField()
    has_downloads = micromodels.BooleanField()
    has_issues = micromodels.BooleanField()
    has_wiki = micromodels.BooleanField()
    homepage = micromodels.CharField()
    html_url = micromodels.CharField()
    language = micromodels.CharField()
    master_branch = micromodels.CharField()
    mirror_url = micromodels.CharField()
    name = micromodels.CharField()
    open_issues = micromodels.IntegerField()
    owner = micromodels.ModelField(User)
    private = micromodels.BooleanField()
    pushed_at = ISODateTimeField()
    size = micromodels.IntegerField()
    url = micromodels.CharField()
    watchers = micromodels.IntegerField()
