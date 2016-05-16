#
# coding=utf-8
"""models - GitHub models for hubugs"""
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

import collections
import datetime

# We used to use tight, explicit bindings for API objects but the desire to
# support Python 3 and the lack of a usable binding library has made it
# necessary to use the loose dynamic binding implemented below.
#
# I fully expect to return to strict binding in the future, once either a tool
# becomes available or I free up a little more itch-scratching time


def object_hook(d, name='unknown'):
    """JSON object hook to create dot-accessible objects.

    :param dict d: Dictionary to operate on
    :param str name: Fallback name, if dict has no ``type`` key
    """
    # FIXME: Dump _links attributes for the time being
    if '_links' in d:
        d.pop('_links')
    for k, v in d.items():
        try:
            d[k] = datetime.datetime.strptime(v, '%Y-%m-%dT%H:%M:%SZ')
        except (TypeError, ValueError):
            pass
    return collections.namedtuple(d.get('type', name), d.keys())(**d)


def _v2_conv_timestamp(s):
    """Parse API v2 style timestamps.

    :param str s: Timestamp to parse
    """
    zone = datetime.timedelta(hours=int(s[-5:-3]))
    stamp = datetime.datetime.strptime(s[:-6], '%Y-%m-%dT%H:%M:%S')
    return (stamp - zone).isoformat() + 'Z'


def from_search(obj):
    """Support legacy API search results as API v3 issues(-ish).

    This is an awful hack to workaround the lack of search support in API
    v3.  It needs to be removed at the first possible opportunity.

    :rtype: ``Issue``
    :returns: API v2 issue mangled to look like a API v3 result
    """

    avatar_url = ('https://secure.gravatar.com/avatar/%s?d='
                  'https://a248.e.akamai.net/assets.github.com%%2F'
                  'images%%2Fgravatars%%2Fgravatar-140.png')
    label_url = 'https://api.github.com/repos/%s/%s/labels/%s'

    owner, project = obj.html_url.split('/')[3:5]

    d = obj.__dict__
    d['id'] = '<from search>'
    d['user'] = {
        'avatar_url': avatar_url % obj.gravatar_id,
        'gravatar_id': obj.gravatar_id,
        'login': obj.user,
        'url': 'https://api.github.com/users/%s' % obj.user,
    }
    if 'closed_by' in obj._fields:
        d['closed_by'] = {
            'avatar_url': avatar_url % obj.closed_by,
            'gravatar_id': obj.gravatar_id,
            'login': obj.user,
            'url': 'https://api.github.com/users/%s' % obj.user,
        }
        d['closed_at'] = _v2_conv_timestamp(obj.closed_at)
    d['created_at'] = _v2_conv_timestamp(obj.created_at)
    d['updated_at'] = _v2_conv_timestamp(obj.updated_at)
    if 'labels' in obj._fields:
        labels = []
        for name in obj.labels:
            labels.append({
                'color': '000000',
                'name': name,
                'url': label_url % (owner, project, name)
            })
        d['labels'] = labels
    return object_hook(d, 'issue')
