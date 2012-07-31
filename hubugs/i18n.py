#
# coding=utf-8
"""i18n - internationalisation support for hubugs"""
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

from os import path

from kitchen.i18n import easy_gettext_setup


PACKAGE_LOCALE = path.join(path.realpath(path.dirname(__file__)), 'locale')

_, N_ = easy_gettext_setup('hubugs', localedirs=[PACKAGE_LOCALE, ])
