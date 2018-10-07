#
"""models - GitHub models for hubugs."""
# Copyright © 2012-2018  James Rowe <jnrowe@gmail.com>
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

import collections
import contextlib
import datetime

from typing import Dict, Optional

from jnrbase.iso_8601 import parse_datetime

# We used to use tight, explicit bindings for API objects but the desire to
# support Python 3 and the lack of a usable binding library has made it
# necessary to use the loose dynamic binding implemented below.
#
# I fully expect to return to strict binding in the future, once either a tool
# becomes available or I free up a little more itch-scratching time


def object_hook(__d: Dict[str, str], __name: Optional[str] = 'unknown'):
    """JSON object hook to create dot-accessible objects.

    Args:
        __d: Dictionary to operate on
        name: Fallback name, if dict has no ``type`` key
    """
    # FIXME: Dump _links attributes for the time being
    if '_links' in __d:
        __d.pop('_links')
    for k, v in __d.items():
        with contextlib.suppress(TypeError, ValueError):
            __d[k] = parse_datetime(v).replace(tzinfo=None)
    return collections.namedtuple(__d.get('type', __name), __d.keys())(**__d)


def _v2_conv_timestamp(__s: str):
    """Parse API v2 style timestamps.

    Args:
        __s: Timestamp to parse
    """
    stamp = parse_datetime(__s).astimezone(datetime.timezone.utc)
    return stamp.isoformat()[:-6] + 'Z'


def from_search(__obj):
    """Support legacy API search results as API v3 issues(-ish).

    This is an awful hack to workaround the lack of search support in API
    v3.  It needs to be removed at the first possible opportunity.

    Returns:
        Issue: API v2 issue mangled to look like a API v3 result
    """

    avatar_url = ('https://secure.gravatar.com/avatar/{}?d='
                  'https://a248.e.akamai.net/assets.github.com%2F'
                  'images%2Fgravatars%2Fgravatar-140.png')
    label_url = 'https://api.github.com/repos/{}/{}/labels/{}'

    owner, project = __obj.html_url.split('/')[3:5]

    d = __obj.__dict__
    d['id'] = '<from search>'
    d['user'] = {
        'avatar_url': avatar_url.format(__obj.gravatar_id),
        'gravatar_id': __obj.gravatar_id,
        'login': __obj.user,
        'url': 'https://api.github.com/users/{}'.format(__obj.user),
    }
    if 'closed_by' in __obj._fields:
        d['closed_by'] = {
            'avatar_url': avatar_url.format(__obj.closed_by),
            'gravatar_id': __obj.gravatar_id,
            'login': __obj.user,
            'url': 'https://api.github.com/users/{}'.format(__obj.user),
        }
        d['closed_at'] = _v2_conv_timestamp(__obj.closed_at)
    d['created_at'] = _v2_conv_timestamp(__obj.created_at)
    d['updated_at'] = _v2_conv_timestamp(__obj.updated_at)
    if 'labels' in __obj._fields:
        labels = []
        for name in __obj.labels:
            labels.append({
                'color': '000000',
                'name': name,
                'url': label_url.format(owner, project, name)
            })
        d['labels'] = labels
    return object_hook(d, 'issue')
